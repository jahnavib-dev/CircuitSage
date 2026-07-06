"""
CircuitSage — Streamlit User Interface
Provides a premium visual interface for datasheet ingestion and multi-agent interaction.
"""

import os
import sys
import tempfile
import json
import asyncio
import streamlit as st
from dotenv import load_dotenv

# Ensure root circuitsage directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

load_dotenv()

from tools.pdf_ingestor import ingest_pdf
from agents.orchestrator import OrchestratorAgent
from memory.session_memory import SessionMemory

# Page Configuration with Premium branding
st.set_page_config(
    page_title="CircuitSage — EE Datasheet Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to run async agent code inside Streamlit
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Fallback if an event loop is already running in the thread
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return loop.run_until_complete(coro)

# Apply Premium Dark Glassmorphic Custom Styling
st.markdown(
    """
    <style>
    /* Dark Theme Canvas Override */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #c9d1d9;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Title Styling */
    .main-title {
        background: linear-gradient(90deg, #58a6ff 0%, #1f6feb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        text-shadow: 0px 4px 20px rgba(88, 166, 255, 0.15);
    }
    .subtitle {
        font-size: 1.1rem;
        color: #8b949e;
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #21262d;
    }
    
    /* Card Glassmorphic container styles */
    .agent-card {
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
    }
    
    /* Sub-Agent Specific Header Styling */
    .query-header {
        color: #58a6ff;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .compare-header {
        color: #ff7b72;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .suggest-header {
        color: #56d364;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .system-header {
        color: #8b949e;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Comparison Table Styling */
    .comp-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 0.95rem;
    }
    .comp-table th {
        background-color: #1f6feb;
        color: white;
        text-align: left;
        padding: 8px 12px;
        border: 1px solid #30363d;
    }
    .comp-table td {
        padding: 8px 12px;
        border: 1px solid #21262d;
        color: #c9d1d9;
    }
    .comp-table tr:nth-child(even) {
        background-color: #161b22;
    }
    
    /* General Button hover transitions */
    div.stButton > button {
        border-radius: 6px;
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #1f6feb;
        color: white;
        border-color: #58a6ff;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar setup matching the specifications
st.sidebar.markdown(
    """
    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 15px;'>
        <span style='font-size: 2rem;'>⚡</span>
        <h1 style='margin: 0; font-size: 2rem; color: #58a6ff; font-weight: 800;'>CircuitSage</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# Gemini API Key Management
api_key_from_env = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key_from_env:
    st.sidebar.warning("🔑 No API Key found in .env. Please supply one below:")
    api_key_input = st.sidebar.text_input("Gemini API Key", type="password", help="Enter your Gemini Developer API Key from Google AI Studio")
else:
    api_key_input = api_key_from_env
    st.sidebar.success("🔑 API Key loaded from environment.")

# Ingestion Panel
st.sidebar.subheader("📥 Ingest Component Datasheets")
uploaded_file = st.sidebar.file_uploader("Upload Datasheet PDF", type=["pdf"])
component_name_input = st.sidebar.text_input("Custom Component Name (Optional)", placeholder="e.g. NE555")

if uploaded_file is not None:
    if st.sidebar.button("Ingest & Vectorize"):
        with st.sidebar.spinner("Processing PDF datasheet..."):
            try:
                # Save uploaded file to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_path = tmp_file.name
                
                # Run ingestion
                # Run ingestion
                num_chunks = ingest_pdf(
                    temp_path,
                    component_name_input if component_name_input else None,
                    original_filename=uploaded_file.name,
                )
                # Cleanup temp file
                os.unlink(temp_path)
                
                st.sidebar.success(f"Successfully ingested {uploaded_file.name}!")
                st.sidebar.balloons()
                st.sidebar.info(f"Generated {num_chunks} vector chunks in ChromaDB.")
            except Exception as e:
                st.sidebar.error(f"Failed to ingest PDF: {e}")

# Session controls
st.sidebar.markdown("---")
st.sidebar.subheader("Session Controls")
session_id = st.sidebar.text_input("Session ID", value="default_session_id")

if st.sidebar.button("Clear Conversation History"):
    memory = SessionMemory(session_id=session_id)
    memory.clear()
    st.success("Conversation history cleared!")
    st.rerun()

# Main Title Area
st.markdown("<h1 class='main-title'>CircuitSage</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>EE Datasheet Intelligence Tool Powered by Google ADK & Gemini 1.5 Flash</p>", unsafe_allow_html=True)

# Check API Key validity before allowing main flow
if not api_key_input:
    st.info("⚠️ Please enter a Gemini API Key in the sidebar or define it in your `.env` file to start using the chatbot.")
else:
    # Initialize the Orchestrator agent dynamically with the API key
    @st.cache_resource
    def get_orchestrator(api_key):
        return OrchestratorAgent(api_key=api_key)
        
    orchestrator = get_orchestrator(api_key_input)
    
    # Load session history
    memory = SessionMemory(session_id=session_id)
    chat_history = memory.get_history()

    # Welcome screen for empty chat
    if not chat_history:
        st.markdown(
            """
            <div class="agent-card" style="background-color: rgba(33, 38, 45, 0.4); border-color: #30363d; margin-top: 40px;">
                <h3>🔌 Welcome to CircuitSage</h3>
                <p>CircuitSage is an agentic electrical engineering datasheet tool. You can ask queries, compare parts, or get recommendations.</p>
                <h5 style="margin-top: 15px; color: #58a6ff;">Example Prompts:</h5>
                <ul>
                    <li><strong>Query:</strong> "What is the maximum operating supply voltage of the NE555?"</li>
                    <li><strong>Compare:</strong> "Compare NE555 and LM741"</li>
                    <li><strong>Suggest:</strong> "Recommend a MOSFET with Vgs < 4.5V and Rds < 50mOhms"</li>
                </ul>
                <p style="font-size: 0.9rem; color: #8b949e;"><em>Note: Please upload components using the sidebar uploader first so that they can be retrieved by similarity search.</em></p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render conversational chat log
    for msg in chat_history:
        role = msg["role"]
        content = msg["content"]
        
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else: # assistant
            # Detect response style (Comparison table vs standard text)
            # If it's Markdown table generated by orchestrator's memory storage, display it
            if "|" in content and "Parameter" in content:
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(
                        f"""
                        <div class="agent-card" style="background-color: rgba(33, 38, 45, 0.4);">
                            <div class="compare-header">📊 CircuitSage·Compare</div>
                            <div style="margin-top: 10px;">
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(content)
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                # Figure out which agent it came from based on text signatures or print standard card
                agent_label = "CircuitSage"
                card_style = "system-header"
                
                if "CircuitSage·Query" in content or "[CircuitSage·Query]" in content:
                    agent_label = "CircuitSage·Query"
                    card_style = "query-header"
                elif "CircuitSage·Compare" in content or "[CircuitSage·Compare]" in content:
                    agent_label = "CircuitSage·Compare"
                    card_style = "compare-header"
                elif "CircuitSage·Suggest" in content or "[CircuitSage·Suggest]" in content:
                    agent_label = "CircuitSage·Suggest"
                    card_style = "suggest-header"
                
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(
                        f"""
                        <div class="agent-card" style="background-color: rgba(33, 38, 45, 0.4);">
                            <div class="{card_style}">⚡ {agent_label}</div>
                            <div style="margin-top: 10px; line-height: 1.6;">
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(content)
                    st.markdown("</div></div>", unsafe_allow_html=True)

    # User Input Field
    user_query = st.chat_input("Ask CircuitSage...")

    if user_query:
        # Display user message instantly
        with st.chat_message("user"):
            st.write(user_query)
            
        # Call the multi-agent orchestrator asynchronously
        with st.spinner("CircuitSage thinking..."):
            try:
                intent, agent_response, extracted_params = run_async(
                    orchestrator.process_user_query(user_query, session_id=session_id)
                )
                
                # Render Assistant reply
                with st.chat_message("assistant", avatar="⚡"):
                    if intent == "compare" and not agent_response.startswith("[CircuitSage"):
                        # Render beautiful HTML comparison table
                        try:
                            comp_list = json.loads(agent_response)
                            table_html = "<table class='comp-table'><tr><th>Parameter</th><th>Component A</th><th>Component B</th></tr>"
                            for row in comp_list:
                                table_html += f"<tr><td>{row['parameter']}</td><td>{row['component_a_value']}</td><td>{row['component_b_value']}</td></tr>"
                            table_html += "</table>"
                            
                            st.markdown(
                                f"""
                                <div class="agent-card" style="background-color: rgba(255, 123, 114, 0.05); border-color: rgba(255, 123, 114, 0.2);">
                                    <div class="compare-header">📊 CircuitSage·Compare</div>
                                    <div style="margin-top: 10px;">
                                        {table_html}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        except Exception:
                            # Fallback if JSON parsing fails
                            st.markdown(
                                f"""
                                <div class="agent-card" style="background-color: rgba(33, 38, 45, 0.4);">
                                    <div class="compare-header">📊 CircuitSage·Compare</div>
                                    <div style="margin-top: 10px;">
                                        {agent_response}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        # Determine special style for suggest or query card
                        card_bg = "rgba(33, 38, 45, 0.4)"
                        border_color = "#30363d"
                        header_class = "system-header"
                        agent_title = "CircuitSage"
                        
                        if intent == "query":
                            card_bg = "rgba(88, 166, 255, 0.05)"
                            border_color = "rgba(88, 166, 255, 0.2)"
                            header_class = "query-header"
                            agent_title = "CircuitSage·Query"
                        elif intent == "suggest":
                            card_bg = "rgba(86, 211, 100, 0.05)"
                            border_color = "rgba(86, 211, 100, 0.2)"
                            header_class = "suggest-header"
                            agent_title = "CircuitSage·Suggest"
                            
                        st.markdown(
                            f"""
                            <div class="agent-card" style="background-color: {card_bg}; border-color: {border_color};">
                                <div class="{header_class}">⚡ {agent_title}</div>
                                <div style="margin-top: 10px; line-height: 1.6;">
                            """,
                            unsafe_allow_html=True
                        )
                        st.markdown(agent_response)
                        st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Rerun to update chat state in history properly
                st.rerun()
            except Exception as e:
                st.error(f"Error executing agent query: {e}")
