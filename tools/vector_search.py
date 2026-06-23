"""
CircuitSage — Vector Search Utility
Queries ChromaDB for relevant datasheet chunks based on semantic similarity.
Supports filtering by component name.
"""

import os
import chromadb
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
COLLECTION_NAME = "circuitsage_datasheets"

# Initialize the embedding model globally
print("[CircuitSage·Search] Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def search_vector_db(query: str, component_name: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the ChromaDB collection for chunks semantically similar to the query.
    """
    # 1. Initialize persistent client and get collection
    db_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Check if collection is empty
    if collection.count() == 0:
        print("[CircuitSage·Search] ChromaDB collection is empty.")
        return []

    # 2. Generate embedding for user query
    query_embedding = embedding_model.encode(query, show_progress_bar=False).tolist()
    
    # 3. Search WITHOUT filter first — get all results
    # then filter manually to avoid casing issues
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 3, collection.count()),
    )
    
    # 4. Format and manually filter by component name
    formatted_results = []
    if results and results.get("documents"):
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
        ids = results["ids"][0]
        
        for i in range(len(documents)):
            meta = metadatas[i]
            # Manual case-insensitive component name filter
            if component_name:
                stored_name = meta.get("component_name", "").upper().strip()
                query_name = component_name.upper().strip()
                if stored_name != query_name:
                    continue
                    
            formatted_results.append({
                "id": ids[i],
                "content": documents[i],
                "metadata": meta,
                "distance": distances[i]
            })
            
            if len(formatted_results) >= top_k:
                break
            
    print(f"[CircuitSage·Search] Query: '{query}' | Component: '{component_name}' | Results: {len(formatted_results)}")
    return formatted_results