"""
CircuitSage — Suggest Specialist Agent
Recommends and ranks electronic components based on constraints (e.g. Vgs, Rds(on), package).
"""
from typing import Optional
import os
import sys
from dotenv import load_dotenv

# Ensure root circuitsage directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

load_dotenv()

from google import genai
from tools.vector_search import search_vector_db

class SuggestAgent:
    """
    SuggestAgent (CircuitSage·Suggest)
    Takes a constraint string, queries ChromaDB for candidate components,
    and returns a ranked recommendations list with reasoning.
    """
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        # Initialize google.genai client directly
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY", "")
        )

    async def suggest_components(self, constraints: str) -> str:
        """
        Suggests matching components based on the given constraint query.
        """
        constraints = constraints.strip()[:500]

        if not constraints:
            return "[CircuitSage·Suggest] Error: Constraints description cannot be empty."

        try:
            print(f"[CircuitSage·Suggest] Searching for components matching: '{constraints}'")

            # Query ChromaDB broadly without component filter
            results = search_vector_db(query=constraints, component_name=None, top_k=8)

            if not results:
                return (
                    "[CircuitSage·Suggest] No component datasheets found in the database. "
                    "Please ingest some datasheets first."
                )

            # Format candidate contexts
            context_blocks = []
            for item in results:
                meta = item["metadata"]
                context_blocks.append(
                    f"--- Candidate: {meta['component_name']} ---\n"
                    f"Source: {meta['filename']} | Page: {meta['page_number']}\n"
                    f"Excerpt: {item['content']}\n"
                )
            context_str = "\n".join(context_blocks)

            prompt = (
                "You are CircuitSage·Suggest, an expert EE component recommendation specialist.\n"
                "Analyze the candidate components from the datasheet excerpts below.\n"
                "Rank them based on how well they match the user's constraints.\n"
                "For each recommendation provide clear engineering reasoning.\n"
                "Cite the source filename and page number for all specs.\n"
                "If no component matches, say so clearly.\n\n"
                f"User Constraints: {constraints}\n\n"
                f"Candidate Components:\n{context_str}\n\n"
                "Provide a numbered ranked list with reasoning."
            )

            response = self.client.models.generate_content(
                model="gemini-1.5-flash-8b",
                contents=prompt
            )

            response_text = response.text.strip()

            if not response_text:
                return "[CircuitSage·Suggest] Error: Received empty response from model."

            return response_text

        except Exception as e:
            print(f"[CircuitSage·Suggest] Exception: {e}")
            return f"[CircuitSage·Suggest] Error: Unable to process recommendation. Details: {str(e)}"