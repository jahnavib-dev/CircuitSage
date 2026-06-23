"""
CircuitSage — Query Specialist Agent
Answers detailed questions about a specific component using retrieved datasheet context.
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

class QueryAgent:
    """
    QueryAgent (CircuitSage·Query)
    Takes a user question and a component name, retrieves relevant datasheet excerpts
    from ChromaDB, and uses Gemini to generate a citation-backed response.
    """
    def __init__(self, api_key: Optional[str] = None):
        # Set API key in environment
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key

        # Initialize google.genai client directly
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY", "")
        )

    async def run_query(self, question: str, component_name: str) -> str:
        """
        Runs a question against datasheet chunks retrieved for a component.
        """
        # Security: Input length capping and sanitization
        question = question.strip()[:500]
        component_name = component_name.strip().upper()[:500]

        if not question:
            return "[CircuitSage·Query] Error: Question cannot be empty."
        if not component_name:
            return "[CircuitSage·Query] Error: Component name must be specified."

        try:
            print(f"[CircuitSage·Query] Searching database for '{component_name}' matching query: '{question}'")

            # 1. Search vector DB for top 6 chunks for this component
            results = search_vector_db(query=question, component_name=component_name, top_k=6)

            if not results:
                return (
                    f"[CircuitSage·Query] No datasheet records found in database for component: '{component_name}'. "
                    "Please ingest the datasheet PDF first."
                )

            # 2. Format database context for the prompt
            context_blocks = []
            for item in results:
                meta = item["metadata"]
                context_blocks.append(
                    f"--- Excerpt ---\n"
                    f"Source File: {meta['filename']}\n"
                    f"Page: {meta['page_number']}\n"
                    f"Content: {item['content']}\n"
                )
            context_str = "\n".join(context_blocks)

            # 3. Build the full prompt
            prompt = (
                "You are CircuitSage·Query, an expert electrical engineering assistant.\n"
                "Answer the question using ONLY the provided datasheet excerpts.\n"
                "Cite the source filename and page number for every fact.\n"
                "Do not make up facts. Use bullet points for specifications.\n\n"
                f"Component: {component_name}\n"
                f"Question: {question}\n\n"
                f"Datasheet Excerpts:\n{context_str}\n\n"
                "Provide a clear, detailed engineering answer with citations."
            )

            # 4. Call Gemini directly
            response = self.client.models.generate_content(
                model="gemini-1.5-flash-8b",
                contents=prompt
            )

            response_text = response.text.strip()

            if not response_text:
                return "[CircuitSage·Query] Error: Received empty response from model."

            return response_text

        except Exception as e:
            print(f"[CircuitSage·Query] Exception encountered: {e}")
            return f"[CircuitSage·Query] Error: Unable to process request. Details: {str(e)}"