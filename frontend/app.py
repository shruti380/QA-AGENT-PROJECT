"""
Streamlit Frontend for QA Agent System - FIXED VERSION
"""
import streamlit as st
import requests
import json
import time
from typing import List, Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="QA Agent - Test Case & Script Generator",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'knowledge_base_built' not in st.session_state:
    st.session_state.knowledge_base_built = False
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'generated_script' not in st.session_state:
    st.session_state.generated_script = None
if 'uploaded_docs' not in st.session_state:
    st.session_state.uploaded_docs = []
if 'uploaded_html' not in st.session_state:
    st.session_state.uploaded_html = None


# Helper functions - FIXED VERSION
def call_api(endpoint: str, method: str = "GET", data: dict = None, files: dict = None, timeout: int = 180):
    """Make API call with timeout and better error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error ({response.status_code}): {response.text}")
            return None
    
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Request timed out after {timeout} seconds. The operation is taking too long.")
        return None
    
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend API. Make sure it's running on http://localhost:8000")
        return None
    
    except Exception as e:
        st.error(f"Unexpected Error: {str(e)}")
        return None


def check_kb_status():
    """Check knowledge base status"""
    result = call_api("/knowledge-base-status", timeout=10)
    if result:
        st.session_state.knowledge_base_built = result.get('built', False)
        return result
    return None


# Main app
def main():
    # Title
    st.title("🤖 Autonomous QA Agent")
    st.markdown("### Test Case & Selenium Script Generator")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        **Step 1:** Upload support documents (MD, TXT, JSON)
        
        **Step 2:** Upload checkout.html
        
        **Step 3:** Build Knowledge Base
        
        **Step 4:** Generate Test Cases
        
        **Step 5:** Generate Selenium Scripts
        """)
        
        st.markdown("---")
        
        # Knowledge Base Status
        st.header("📊 Status")
        kb_status = check_kb_status()
        if kb_status:
            if kb_status['built']:
                st.success("✓ Knowledge Base Ready")
                st.info(f"Documents: {kb_status['document_count']}")
                
                if kb_status.get('sources'):
                    with st.expander("View Sources"):
                        for source, count in kb_status['sources'].items():
                            st.text(f"• {source}: {count} chunks")
            else:
                st.warning("⚠ Knowledge Base Not Built")
        
        st.markdown("---")
        
        # Clear All button
        if st.button("🗑️ Clear All Data", type="secondary"):
            with st.spinner("Clearing data..."):
                result = call_api("/clear-all", "POST", timeout=30)
                if result and result.get('success'):
                    st.session_state.knowledge_base_built = False
                    st.session_state.test_cases = []
                    st.session_state.generated_script = None
                    st.session_state.uploaded_docs = []
                    st.session_state.uploaded_html = None
                    st.success("All data cleared!")
                    time.sleep(1)
                    st.rerun()
    
    # Main content
    
    # Section 1: File Upload
    st.header("📁 Step 1: Upload Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Support Documents")
        st.markdown("Upload product specs, UI/UX guides, API docs (MD, TXT, JSON)")
        
        uploaded_docs = st.file_uploader(
            "Choose files",
            type=['md', 'txt', 'json'],
            accept_multiple_files=True,
            key="doc_uploader"
        )
        
        if uploaded_docs:
            if st.button("Upload Documents", type="primary"):
                with st.spinner("Uploading documents..."):
                    files = [("files", (doc.name, doc, doc.type)) for doc in uploaded_docs]
                    result = call_api("/upload-documents", "POST", files=files, timeout=60)
                    
                    if result and result.get('success'):
                        st.session_state.uploaded_docs = [f['filename'] for f in result['files']]
                        st.success(f"✓ Uploaded {len(uploaded_docs)} documents")
                    else:
                        st.error("Upload failed")
        
        if st.session_state.uploaded_docs:
            with st.expander("Uploaded Documents"):
                for doc in st.session_state.uploaded_docs:
                    st.text(f"• {doc}")
    
    with col2:
        st.subheader("HTML File")
        st.markdown("Upload checkout.html for script generation")
        
        uploaded_html = st.file_uploader(
            "Choose HTML file",
            type=['html'],
            key="html_uploader"
        )
        
        if uploaded_html:
            if st.button("Upload HTML", type="primary"):
                with st.spinner("Uploading HTML..."):
                    files = {"file": (uploaded_html.name, uploaded_html, "text/html")}
                    result = call_api("/upload-html", "POST", files=files, timeout=30)
                    
                    if result and result.get('success'):
                        st.session_state.uploaded_html = uploaded_html.name
                        st.success(f"✓ Uploaded {uploaded_html.name}")
                    else:
                        st.error("Upload failed")
        
        if st.session_state.uploaded_html:
            st.info(f"📄 HTML: {st.session_state.uploaded_html}")
    
    st.markdown("---")
    
    # Section 2: Build Knowledge Base
    st.header("🔨 Step 2: Build Knowledge Base")
    
    if st.session_state.uploaded_docs or st.session_state.uploaded_html:
        if st.button("🚀 Build Knowledge Base", type="primary", use_container_width=True):
            with st.spinner("Processing documents and building vector database..."):
                progress_bar = st.progress(0)
                
                # Simulate progress
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                
                result = call_api("/build-knowledge-base", "POST", timeout=120)
                
                if result and result.get('success'):
                    st.session_state.knowledge_base_built = True
                    st.success("✅ Knowledge Base Built Successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Files Processed", len(result.get('processed_files', [])))
                    with col2:
                        st.metric("Total Chunks", result.get('total_chunks', 0))
                    with col3:
                        st.metric("Vector Dimension", result.get('statistics', {}).get('dimension', 0))
                    
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to build knowledge base")
    else:
        st.info("⚠ Please upload documents and HTML file first")
    
    st.markdown("---")
    
    # Section 3: Generate Test Cases
    if st.session_state.knowledge_base_built:
        st.header("🧪 Step 3: Generate Test Cases")
        
        # Suggested queries
        st.subheader("Quick Start Queries")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💰 Discount Codes", use_container_width=True):
                st.session_state.test_query = "Generate test cases for discount code feature"
        
        with col2:
            if st.button("📋 Form Validation", use_container_width=True):
                st.session_state.test_query = "Generate test cases for form validation"
        
        with col3:
            if st.button("🛒 Shopping Cart", use_container_width=True):
                st.session_state.test_query = "Generate test cases for shopping cart functionality"
        
        # Query input
        query = st.text_input(
            "Enter your test case request",
            value=st.session_state.get('test_query', ''),
            placeholder="E.g., Generate test cases for payment methods"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            num_cases = st.slider("Number of test cases", 1, 15, 10)
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            generate_btn = st.button("🎯 Generate Test Cases", type="primary", use_container_width=True)
        
        if generate_btn and query:
            with st.spinner("Generating test cases with AI..."):
                data = {
                    "query": query,
                    "num_cases": num_cases
                }
                result = call_api("/generate-test-cases", "POST", data=data, timeout=120)
                
                if result and result.get('success'):
                    st.session_state.test_cases = result['test_cases']
                    st.success(f"✅ Generated {len(st.session_state.test_cases)} test cases!")
                else:
                    st.error("Failed to generate test cases")
        
        # Display test cases
        if st.session_state.test_cases:
            st.subheader("Generated Test Cases")
            
            for i, tc in enumerate(st.session_state.test_cases):
                with st.expander(f"**{tc['test_id']}** - {tc['test_scenario']}", expanded=(i == 0)):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Feature:** {tc['feature']}")
                        st.markdown(f"**Type:** {tc.get('test_type', 'positive').title()}")
                        
                        st.markdown("**Test Steps:**")
                        for j, step in enumerate(tc['test_steps'], 1):
                            st.markdown(f"{j}. {step}")
                        
                        st.markdown(f"**Expected Result:**")
                        st.info(tc['expected_result'])
                        
                        st.markdown(f"**Grounded In:**")
                        st.caption(tc['grounded_in'])
                    
                    with col2:
                        if st.button(f"Generate Script 📝", key=f"gen_script_{i}", use_container_width=True):
                            st.session_state.selected_test_case = tc
                            st.session_state.show_script_section = True
                            st.rerun()
            
            # Download JSON
            if st.button("📥 Download Test Cases (JSON)", use_container_width=True):
                json_str = json.dumps(st.session_state.test_cases, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="test_cases.json",
                    mime="application/json"
                )
        
        st.markdown("---")
    
    # Section 4: Generate Selenium Script - FIXED VERSION
    if st.session_state.knowledge_base_built and st.session_state.get('show_script_section'):
        st.header("🎬 Step 4: Generate Selenium Script")
        
        if 'selected_test_case' in st.session_state:
            tc = st.session_state.selected_test_case
            
            st.info(f"Generating script for: **{tc['test_id']}** - {tc['test_scenario']}")
            
            html_path = st.text_input(
                "HTML File Path (update path for your system)",
                value="C:/Users/shrut/Documents/qa-agent-project/data/uploads/checkout.html",
                help="Update this path to match your local system"
            )
            
            if st.button("⚡ Generate Selenium Script", type="primary", use_container_width=True):
                # Progress indicators
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                try:
                    status_placeholder.info("🔄 Sending request to AI...")
                    progress_bar = progress_placeholder.progress(0)
                    
                    # Start timer
                    start_time = time.time()
                    
                    data = {
                        "test_case": tc,
                        "html_file_path": html_path
                    }
                    
                    progress_bar.progress(20)
                    status_placeholder.info("⏳ Waiting for AI to generate script... (this may take 30-60 seconds)")
                    
                    # Make API call with 3 minute timeout
                    result = call_api("/generate-script", "POST", data=data, timeout=180)
                    
                    elapsed = time.time() - start_time
                    
                    if result and result.get('success'):
                        progress_bar.progress(100)
                        status_placeholder.success(f"✅ Script generated in {elapsed:.1f} seconds!")
                        
                        st.session_state.generated_script = result['script']
                        st.session_state.script_filename = result['filename']
                        
                        time.sleep(2)
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        st.rerun()
                    else:
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        st.error("Failed to generate script. Check the logs above for details.")
                
                except Exception as e:
                    progress_placeholder.empty()
                    status_placeholder.empty()
                    st.error(f"Error: {str(e)}")
            
            # Display generated script
            if st.session_state.generated_script:
                st.subheader("Generated Selenium Script")
                
                # Show code
                st.code(st.session_state.generated_script, language='python')
                
                col1, col2 = st.columns(2)
                with col1:
                    # Download button
                    st.download_button(
                        label="📥 Download Script",
                        data=st.session_state.generated_script,
                        file_name=st.session_state.get('script_filename', 'test_script.py'),
                        mime="text/x-python",
                        use_container_width=True
                    )
                
                with col2:
                    # Copy to clipboard info
                    st.info("💡 Copy the script above and save as .py file")
                
                # Usage instructions
                with st.expander("📖 How to Run This Script"):
                    st.markdown("""
                    ### Prerequisites
                    ```bash
                    pip install selenium
                    ```
                    
                    ### Update the HTML path in the script
                    Find this line in the script:
                    ```python
                    self.driver.get("file:///path/to/checkout.html")
                    ```
                    Replace with your actual file path.
                    
                    ### Run the script
                    ```bash
                    python test_script.py
                    ```
                    
                    ### WebDriver Setup
                    Make sure you have ChromeDriver or GeckoDriver installed and in your PATH.
                    """)


if __name__ == "__main__":
    main()