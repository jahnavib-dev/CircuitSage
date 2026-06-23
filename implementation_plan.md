# CircuitSage — EE Datasheet Intelligence Tool

CircuitSage is a multi-agent Electrical Engineering (EE) datasheet intelligence tool built using the **Google ADK** (Agent Development Kit), **Gemini 1.5 Flash**, **ChromaDB**, and **Streamlit**. It provides automated PDF datasheet ingestion, vector similarity search, and three specialized agents coordinated by a master Orchestrator agent with session memory.

---

## User Review Required

> [!IMPORTANT]
> - **API Credentials**: The tool requires `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) to be set in the `.env` file to query the Gemini 1.5 Flash model.
> - **Dependencies**: `google-adk` depends on the new `google-genai` SDK. We will install compatible versions of all libraries.
> - **MCP Server**: The MCP server uses `FastMCP` running over SSE transport on `localhost:8000`.

---

## Proposed Changes

### Project Structure
We will create the following folder structure:
```
circuitsage/
├── agents/
│   ├── orchestrator.py      # Master agent with session memory & routing logic
│   ├── query_agent.py       # Specialist for datasheet similarity QA (CircuitSage·Query)
│   ├── compare_agent.py     # Specialist for structural spec comparison (CircuitSage·Compare)
│   └── suggest_agent.py     # Specialist for constraint-based recommendations (CircuitSage·Suggest)
├── tools/
│   ├── pdf_ingestor.py      # PDF parsing, splitting, embedding, and database storage
│   ├── vector_search.py     # Similarity search tool querying ChromaDB
│   └── mcp_server.py        # FastMCP server exposing pdf_ingestor on localhost:8000
├── memory/
│   └── session_memory.py    # Class to maintain the last 10 turns of interaction
├── ui/
│   └── app.py               # Streamlit web interface with visual cards and file uploads
├── data/
│   └── chroma_db/           # Local persistent directory for ChromaDB database
├── CONTEXT.md               # Strict security & coding rules
├── README.md                # Project documentation, architecture, and setup instructions
├── .env.example             # Example environment configuration
└── requirements.txt         # Precise python dependencies
```

---

### Component Details

#### 1. Core Tools
*   `tools/pdf_ingestor.py`
    *   Uses `langchain_community.document_loaders.PyPDFLoader` to load datasheets.
    *   Uses `RecursiveCharacterTextSplitter` with `chunk_size=500` and `chunk_overlap=50`.
    *   Uses `sentence-transformers/all-MiniLM-L6-v2` to generate local embeddings.
    *   Persists embeddings to ChromaDB under `data/chroma_db` with metadata: `{filename, page_number, component_name}`.
*   `tools/vector_search.py`
    *   Helper to embed queries and perform similarity search on ChromaDB, applying optional filtering on `component_name`.
*   `tools/mcp_server.py`
    *   Exposes `pdf_ingestor.py`'s functionality via `FastMCP` running on `localhost:8000`.

#### 2. Session Memory
*   `memory/session_memory.py`
    *   Maintains the conversation history (last 10 turns).
    *   Enables context-aware intent classification (e.g. answering follow-up queries that refer to previously mentioned parts).

#### 3. Agents
*   `agents/orchestrator.py`
    *   Uses Gemini 1.5 Flash to classify the query into `"query"`, `"compare"`, or `"suggest"`, extracting relevant entities (component names, questions, constraints).
    *   Invokes the corresponding specialist agent and returns the output.
*   `agents/query_agent.py` (`CircuitSage·Query`)
    *   Extracts answers using ChromaDB datasheet context, providing exact page numbers and PDF source file citations.
*   `agents/compare_agent.py` (`CircuitSage·Compare`)
    *   Performs spec lookup on two components and generates a structured comparison dictionary with parameters, component A values, and component B values.
*   `agents/suggest_agent.py` (`CircuitSage·Suggest`)
    *   Filters components based on constraints (e.g., Vgs, Rds(on), packages) using vector-backed retrieval, returning a ranked recommendation list with reasoning.

#### 4. Streamlit UI
*   `ui/app.py`
    *   Stunning modern UI with custom branding.
    *   Sidebar containing local file upload capabilities for direct datasheet ingestion.
    *   A chat interface showing responses wrapped in custom styled cards based on the responding agent.

#### 5. Configuration & Quality Assurance
*   `CONTEXT.md`: Strict rules against hardcoding secrets, ensuring input sanitization (capping length to 500 characters), and logging conventions.
*   `requirements.txt`: Curated dependency versions.
*   `README.md`: Thorough explanation of setup, usage, and system flow.

---

## Verification Plan

### Automated Verification
*   We will run a test script (`test_agents.py`) to verify:
    1. Ingestion of a sample datasheet.
    2. Intent classification and routing.
    3. Proper search and response generation by sub-agents.
    4. Compliance with input length restrictions (500 characters).

### Manual Verification
*   Launch Streamlit UI locally: `streamlit run ui/app.py`.
*   Validate PDF ingestion, query answering with citations, comparison tables, and component suggestion matching.
*   Verify that agent cards render the correct prefix (`CircuitSage·Query`, `CircuitSage·Compare`, `CircuitSage·Suggest`).
