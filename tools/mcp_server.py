"""
CircuitSage — MCP Server
Exposes the CircuitSage PDF ingestor as a Model Context Protocol (MCP) tool.
Runs on localhost:8000.
"""

import os
import sys
from fastmcp import FastMCP

# Ensure the root circuitsage directory is in sys.path for clean imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.pdf_ingestor import ingest_pdf

# 1. Initialize the FastMCP server with our branding
mcp = FastMCP(
    "CircuitSage",
    title="CircuitSage Datasheet Ingestion Server",
    description="MCP Server exposing datasheet ingestion functionality for CircuitSage"
)

# 2. Define the ingestion tool
@mcp.tool()
def ingest_datasheet(pdf_path: str, component_name: str = "") -> str:
    """Ingests an EE component datasheet PDF into the CircuitSage vector database.
    
    Args:
        pdf_path: The absolute file path to the PDF datasheet on disk.
        component_name: Optional. The name of the electrical component (e.g. 'NE555').
                        If not provided, the name is inferred from the PDF filename.
                        
    Returns:
        A success message with the number of ingested chunks, or an error message.
    """
    # Security: Sanitization & Input Length Check
    # Cap inputs at 500 characters
    if not pdf_path:
        return "[CircuitSage·MCP] Error: PDF path cannot be empty."
        
    pdf_path = pdf_path.strip()
    if len(pdf_path) > 500:
        return "[CircuitSage·MCP] Error: PDF path exceeds 500 character limit."
        
    if component_name:
        component_name = component_name.strip()
        if len(component_name) > 500:
            return "[CircuitSage·MCP] Error: Component name exceeds 500 character limit."

    # Verify file existence
    if not os.path.exists(pdf_path):
        return f"[CircuitSage·MCP] Error: PDF file not found at local path '{pdf_path}'."
        
    if not pdf_path.lower().endswith(".pdf"):
        return "[CircuitSage·MCP] Error: Target file must be a PDF document."

    try:
        # Ingest PDF
        num_chunks = ingest_pdf(pdf_path, component_name if component_name else None)
        return (
            f"[CircuitSage·MCP] Success: Ingested '{pdf_path}' into ChromaDB. "
            f"Extracted and embedded {num_chunks} chunks."
        )
    except Exception as e:
        # Handle exceptions gracefully
        return f"[CircuitSage·MCP] Error during ingestion: {str(e)}"

# 3. Start the server when executed directly
if __name__ == "__main__":
    print("[CircuitSage·MCP] Starting FastMCP Server on localhost:8000...")
    # Use standard SSE transport running on localhost:8000
    mcp.run(transport="sse", host="localhost", port=8000)
