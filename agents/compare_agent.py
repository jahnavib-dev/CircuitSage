"""
CircuitSage — Compare Specialist Agent
Extracts and compares specifications between two electronic components.
Returns a structured JSON comparison list.
"""
from typing import Optional, List, Dict, Any
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
from tools.vector_search import search_vector_db

class CompareAgent:
    """
    CompareAgent (CircuitSage·Compare)
    Takes two component names, retrieves their specifications from ChromaDB,
    and returns a structured comparison list.
    """
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        # Initialize google.genai client directly
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY", "")
        )

    async def compare_components(self, component_a: str, component_b: str) -> List[Dict[str, Any]]:
        """
        Compares two components by fetching their specifications from ChromaDB.
        """
        component_a = component_a.strip().upper()[:500]
        component_b = component_b.strip().upper()[:500]

        if not component_a or not component_b:
            raise ValueError("[CircuitSage·Compare] Error: Both component names must be specified.")

        try:
            print(f"[CircuitSage·Compare] Retrieving specs for: '{component_a}' and '{component_b}'")

            spec_query = "specifications electrical characteristics maximum ratings parameters operating conditions"

            results_a = search_vector_db(query=spec_query, component_name=component_a, top_k=5)
            results_b = search_vector_db(query=spec_query, component_name=component_b, top_k=5)

            if not results_a and not results_b:
                return [{"parameter": "Error", "component_a_value": f"No datasheet for '{component_a}'", "component_b_value": f"No datasheet for '{component_b}'"}]
            elif not results_a:
                return [{"parameter": "Error", "component_a_value": f"No datasheet for '{component_a}'", "component_b_value": "Found"}]
            elif not results_b:
                return [{"parameter": "Error", "component_a_value": "Found", "component_b_value": f"No datasheet for '{component_b}'"}]

            context_a = "\n".join([f"Source: {i['metadata']['filename']} Page: {i['metadata']['page_number']}\n{i['content']}" for i in results_a])
            context_b = "\n".join([f"Source: {i['metadata']['filename']} Page: {i['metadata']['page_number']}\n{i['content']}" for i in results_b])

            prompt = (
                "You are CircuitSage·Compare, an expert EE comparison specialist.\n"
                "Compare the two components using ONLY the provided datasheet excerpts.\n"
                "Return ONLY a JSON list of dicts with keys: parameter, component_a_value, component_b_value.\n"
                "No markdown, no backticks, no extra text.\n\n"
                f"Component A: {component_a}\n"
                f"Component B: {component_b}\n\n"
                f"Excerpts for {component_a}:\n{context_a}\n\n"
                f"Excerpts for {component_b}:\n{context_b}\n\n"
                "Output JSON list only."
            )

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            cleaned = response.text.strip()
            if cleaned.startswith("```"):
                match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1).strip()

            comparison_list = json.loads(cleaned)

            validated = []
            for item in comparison_list:
                if isinstance(item, dict) and "parameter" in item:
                    validated.append({
                        "parameter": str(item.get("parameter", "")),
                        "component_a_value": str(item.get("component_a_value", "N/A")),
                        "component_b_value": str(item.get("component_b_value", "N/A"))
                    })

            return validated

        except Exception as e:
            print(f"[CircuitSage·Compare] Exception: {e}")
            return [{"parameter": "Exception", "component_a_value": "Failed", "component_b_value": str(e)}]