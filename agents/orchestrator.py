"""
CircuitSage — Orchestrator Agent
Acts as the central routing hub, detects user intent, maintains session memory,
and delegates processing to sub-agents.
"""
from typing import Optional, Dict, Any, Tuple
import os
import sys
import json
import re
from dotenv import load_dotenv

# Ensure root circuitsage directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

load_dotenv()

from google import genai
from google.genai import types
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from memory.session_memory import SessionMemory
from agents.query_agent import QueryAgent
from agents.compare_agent import CompareAgent
from agents.suggest_agent import SuggestAgent

class OrchestratorAgent:
    """
    OrchestratorAgent (CircuitSage·Orchestrator)
    Detects user intent from query using Gemini and routes to the correct specialist agent.
    Supported intent categories: "query", "compare", "suggest".
    Manages session memory (up to last 10 turns).
    """
    def __init__(self, api_key: Optional[str] = None):
        # Set API key in environment so ADK picks it up automatically
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        # Initialize sub-agents
        self.query_agent = QueryAgent(api_key=api_key)
        self.compare_agent = CompareAgent(api_key=api_key)
        self.suggest_agent = SuggestAgent(api_key=api_key)

        # Initialize google.genai client for direct classification calls
        self.genai_client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY", "")
        )

    async def classify_intent(self, user_query: str, history_str: str) -> Dict[str, Any]:
        """
        Calls Gemini directly via google.genai to classify intent and extract parameters.
        """
        prompt = (
            "You are a routing classifier for an EE datasheet tool.\n"
            "Classify the intent and extract parameters from the user query.\n\n"
            "Rules:\n"
            "- component_name must ONLY be an electronic part number like NE555, LM358, IRF540N\n"
            "- component_name must NEVER be English words like MAXIMUM, SUPPLY, VOLTAGE, WHAT\n"
            "- Return ONLY a JSON object, no markdown, no backticks\n\n"
            "JSON keys required:\n"
            "- intent: 'query', 'compare', or 'suggest'\n"
            "- component_name: part number or empty string\n"
            "- question: technical question or empty string\n"
            "- component_a: first component for compare or empty string\n"
            "- component_b: second component for compare or empty string\n"
            "- constraints: constraint string for suggest or empty string\n\n"
            "Examples:\n"
            "Query: 'What is the maximum supply voltage of the NE555?'\n"
            "Output: {\"intent\": \"query\", \"component_name\": \"NE555\", \"question\": \"What is the maximum supply voltage?\", \"component_a\": \"\", \"component_b\": \"\", \"constraints\": \"\"}\n\n"
            "Query: 'Compare NE555 and LM358'\n"
            "Output: {\"intent\": \"compare\", \"component_name\": \"\", \"question\": \"\", \"component_a\": \"NE555\", \"component_b\": \"LM358\", \"constraints\": \"\"}\n\n"
            "Query: 'Recommend a MOSFET with Vgs less than 4.5V'\n"
            "Output: {\"intent\": \"suggest\", \"component_name\": \"\", \"question\": \"\", \"component_a\": \"\", \"component_b\": \"\", \"constraints\": \"MOSFET, Vgs < 4.5V\"}\n\n"
            f"Now classify this query: {user_query}"
        )

        try:
            response = self.genai_client.models.generate_content(
                model="gemini-1.5-flash-8b",
                contents=prompt
            )
            cleaned = response.text.strip()
            print(f"[CircuitSage·Orchestrator] Raw Gemini response: {cleaned}")

            # Strip markdown if present
            if cleaned.startswith("```"):
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1).strip()

            classification = json.loads(cleaned)
            return classification

        except Exception as e:
            print(f"[CircuitSage·Orchestrator] Classification failed: {e}")
            # Smart fallback using strict part number regex
            matches = re.findall(r"\b[A-Za-z]{1,4}[0-9]{2,6}[A-Za-z0-9]{0,5}\b", user_query)
            component = matches[0].upper() if matches else ""
            return {
                "intent": "query",
                "component_name": component,
                "question": user_query,
                "component_a": "",
                "component_b": "",
                "constraints": ""
            }

    async def process_user_query(self, user_query: str, session_id: str = "default_session") -> Tuple[str, str, Dict[str, Any]]:
        """
        Processes a user query by classifying intent, routing to correct sub-agent,
        and maintaining conversation session memory.
        """
        # Security: Input length capped at 500 characters
        user_query = user_query.strip()[:500]
        if not user_query:
            return "query", "[CircuitSage] Input query cannot be empty.", {}

        # 1. Initialize/Load session memory
        memory = SessionMemory(session_id=session_id)
        history = memory.get_history()

        # Format history for classifier context
        history_str_list = []
        for msg in history:
            history_str_list.append(f"{msg['role'].upper()}: {msg['content']}")
        history_str = "\n".join(history_str_list)

        # 2. Run intent classification
        classification = await self.classify_intent(user_query, history_str)
        intent = classification.get("intent", "query")

        print(f"[CircuitSage·Orchestrator] Detected Intent: '{intent}' | Classification: {classification}")

        # 3. Route to the appropriate sub-agent
        response_content = ""

        if intent == "compare":
            comp_a = classification.get("component_a", "").strip()
            comp_b = classification.get("component_b", "").strip()

            # Fallback: extract part numbers from query using strict regex
            if not comp_a or not comp_b:
                matches = re.findall(r"\b[A-Za-z]{1,4}[0-9]{2,6}[A-Za-z0-9]{0,5}\b", user_query)
                parts = [m.upper() for m in matches]
                if len(parts) >= 2:
                    comp_a, comp_b = parts[0], parts[1]

            if not comp_a or not comp_b:
                response_content = (
                    "[CircuitSage·Compare] Error: Could not extract two components from your query. "
                    "Example: 'Compare NE555 and LM358'"
                )
            else:
                comparison_result = await self.compare_agent.compare_components(comp_a, comp_b)
                response_content = json.dumps(comparison_result)

        elif intent == "suggest":
            constraints = classification.get("constraints", "").strip()
            if not constraints:
                constraints = user_query
            response_content = await self.suggest_agent.suggest_components(constraints)

        else:  # intent == "query"
            component = classification.get("component_name", "").strip()
            question = classification.get("question", "").strip()

            # Fallback 1: check history for component name
            if not component and history:
                for msg in reversed(history):
                    if msg["role"] == "user":
                        matches = re.findall(r"\b[A-Za-z]{1,4}[0-9]{2,6}[A-Za-z0-9]{0,5}\b", msg["content"])
                        if matches:
                            component = matches[0].upper()
                            break

            # Fallback 2: extract from current query using strict part number regex
            if not component:
                matches = re.findall(r"\b[A-Za-z]{1,4}[0-9]{2,6}[A-Za-z0-9]{0,5}\b", user_query)
                if matches:
                    component = matches[0].upper()

            if not question:
                question = user_query

            if not component:
                response_content = (
                    "[CircuitSage·Query] Error: I need a component name to answer your query. "
                    "Example: 'What is the pinout of NE555?'"
                )
            else:
                response_content = await self.query_agent.run_query(question, component)

        # 4. Save to session memory
        memory_content = response_content
        if intent == "compare" and not response_content.startswith("[CircuitSage"):
            try:
                comp_list = json.loads(response_content)
                table_lines = ["| Parameter | Component A | Component B |", "| --- | --- | --- |"]
                for row in comp_list:
                    table_lines.append(f"| {row['parameter']} | {row['component_a_value']} | {row['component_b_value']} |")
                memory_content = "\n".join(table_lines)
            except Exception:
                pass

        memory.add_message("user", user_query)
        memory.add_message("assistant", memory_content)

        return intent, response_content, classification