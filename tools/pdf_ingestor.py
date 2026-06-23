"""
CircuitSage — PDF Ingestor
Loads, chunks, and embeds PDF datasheets, storing the resulting vectors in ChromaDB.
"""

import os
import uuid
import chromadb
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Load configurations
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
COLLECTION_NAME = "circuitsage_datasheets"

# Initialize SentenceTransformer embedding model globally
# all-MiniLM-L6-v2 produces 384-dimensional dense vectors
print("[CircuitSage·Ingestor] Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def ingest_pdf(pdf_path: str, component_name: Optional[str] = None) -> int:
    """
    Loads a PDF datasheet, splits it into chunks of size 500 with 50 overlap,
    generates embeddings using sentence-transformers, and stores them in ChromaDB.
    
    Args:
        pdf_path: Path to the target PDF datasheet.
        component_name: Optional custom component name. If None, derived from filename.
        
    Returns:
        The total number of chunks ingested.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Datasheet file not found at {pdf_path}")

    # Derived component name from file name if not provided
    filename = os.path.basename(pdf_path)
    if not component_name:
        component_name = os.path.splitext(filename)[0]
    
    # Standardize component name (uppercase, trimmed)
    component_name = component_name.strip().upper()

    print(f"[CircuitSage·Ingestor] Loading PDF: {filename} for component: {component_name}")
    
    # 1. Parse PDF using PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    
    # 2. Split pages into character-level chunks (chunk_size=500, overlap=50)
    # Using RecursiveCharacterTextSplitter to maintain semantic boundaries (paragraphs, lines)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    
    chunks = []
    metadatas = []
    ids = []
    
    for page in pages:
        page_content = page.page_content
        page_num = page.metadata.get("page", 0) + 1  # 1-indexed for reader clarity
        
        # Split page content
        page_chunks = text_splitter.split_text(page_content)
        
        for i, chunk_text in enumerate(page_chunks):
            # Check length constraint
            if not chunk_text.strip():
                continue
                
            chunks.append(chunk_text)
            metadatas.append({
                "filename": filename,
                "page_number": page_num,
                "component_name": component_name
            })
            # Generate unique ID for each chunk
            ids.append(f"{component_name}_{page_num}_{i}_{str(uuid.uuid4())[:8]}")

    if not chunks:
        print("[CircuitSage·Ingestor] No text chunks found in PDF.")
        return 0

    print(f"[CircuitSage·Ingestor] Generating embeddings for {len(chunks)} chunks...")
    
    # 3. Create embeddings manually using sentence-transformers
    embeddings = embedding_model.encode(chunks, show_progress_bar=False)
    
    # 4. Initialize ChromaDB client and store
    db_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = db_client.get_or_create_collection(name=COLLECTION_NAME)
    
    # Add items to ChromaDB collection
    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        documents=chunks
    )
    
    print(f"[CircuitSage·Ingestor] Successfully ingested {len(chunks)} chunks for {component_name}.")
    return len(chunks)
