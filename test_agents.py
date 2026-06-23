"""
CircuitSage — Test Suite
Inserts mock datasheet data into ChromaDB and runs validation tests on all specialist agents
and the central Orchestrator routing loop.
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Ensure root circuitsage directory is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

load_dotenv()

import chromadb
from sentence_transformers import SentenceTransformer
from agents.orchestrator import OrchestratorAgent

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def populate_mock_data():
    """Populates ChromaDB with mock datasheet records for testing."""
    print("[CircuitSage·Test] Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path="data/chroma_db")
    collection = client.get_or_create_collection("circuitsage_datasheets")
    
    # Check if empty, then populate
    if collection.count() == 0:
        print("[CircuitSage·Test] Database is empty. Injecting mock component records...")
        docs = [
            "NE555 Precision Timer datasheet. Maximum supply voltage VCC is 16V. Operating supply current is 10mA. Operating temperature range is 0 to 70 C. Package options: 8-pin PDIP, 8-pin SOIC.",
            "LM358 Dual Operational Amplifier. Maximum supply voltage is 32V. Supply current is 500 uA. Package is SOIC-8 or PDIP-8. Input offset voltage is 2mV.",
            "IRF540 N-Channel Power MOSFET. Drain-to-Source Voltage Vds max is 100V. Gate threshold voltage Vgs(th) max is 4.0V. Rds(on) max is 44 mOhms. Continuous drain current is 33A. Package is TO-220."
        ]
        metadatas = [
            {"filename": "ne555.pdf", "page_number": 1, "component_name": "NE555"},
            {"filename": "lm358.pdf", "page_number": 2, "component_name": "LM358"},
            {"filename": "irf540.pdf", "page_number": 1, "component_name": "IRF540"}
        ]
        ids = ["mock_ne555", "mock_lm358", "mock_irf540"]
        
        print("[CircuitSage·Test] Generating sentence embeddings...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(docs).tolist()
        
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=docs)
        print(f"[CircuitSage·Test] Successfully populated {collection.count()} mock documents.")
    else:
        print(f"[CircuitSage·Test] Database already contains {collection.count()} records.")

async def run_tests():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[CircuitSage·Test] Error: GEMINI_API_KEY is not set. Cannot run agent tests.")
        return
        
    print("[CircuitSage·Test] Initializing OrchestratorAgent...")
    orchestrator = OrchestratorAgent(api_key=api_key)
    
    # Test 1: Query Specialist
    print("\n--- TEST 1: Query Specialist (CircuitSage·Query) ---")
    query = "What is the maximum supply voltage of the NE555?"
    print(f"User: {query}")
    intent, response, params = await orchestrator.process_user_query(query, session_id="test_session")
    print(f"Detected Intent: {intent}")
    print(f"Extracted Params: {params}")
    print(f"Agent Response:\n{response}")
    
    # Test 2: Compare Specialist
    print("\n--- TEST 2: Compare Specialist (CircuitSage·Compare) ---")
    query = "Compare NE555 and LM358 specs"
    print(f"User: {query}")
    intent, response, params = await orchestrator.process_user_query(query, session_id="test_session")
    print(f"Detected Intent: {intent}")
    print(f"Extracted Params: {params}")
    try:
        parsed_comp = json.loads(response)
        print("Agent Structured Comparison Table Output:")
        print(json.dumps(parsed_comp, indent=2))
    except Exception:
        print(f"Agent Response (unparsed):\n{response}")
        
    # Test 3: Suggest Specialist
    print("\n--- TEST 3: Suggest Specialist (CircuitSage·Suggest) ---")
    query = "Recommend a component with Vds > 50V and Rds < 50mOhms"
    print(f"User: {query}")
    intent, response, params = await orchestrator.process_user_query(query, session_id="test_session")
    print(f"Detected Intent: {intent}")
    print(f"Extracted Params: {params}")
    print(f"Agent Response:\n{response}")
    
    # Test 4: Session Context Resolution
    print("\n--- TEST 4: Session context resolution ---")
    # First query to establish NE555 context
    await orchestrator.process_user_query("What is the supply current of NE555?", session_id="context_session")
    # Follow-up query referring to 'its'
    query = "What package types does it support?"
    print(f"User: {query}")
    intent, response, params = await orchestrator.process_user_query(query, session_id="context_session")
    print(f"Detected Intent: {intent}")
    print(f"Extracted Params: {params}")
    print(f"Agent Response:\n{response}")

if __name__ == "__main__":
    populate_mock_data()
    asyncio.run(run_tests())
