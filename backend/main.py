"""
FastAPI Backend for QA Agent System
"""
import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.groq_client import GroqClient, get_groq_client
from backend.document_processor import DocumentProcessor
from backend.vector_store import VectorStore
from backend.test_case_generator import TestCaseGenerator
from backend.script_generator import ScriptGenerator


# Initialize FastAPI app
app = FastAPI(
    title="QA Agent API",
    description="Autonomous QA Agent for Test Case and Script Generation",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
vector_store = None
llm_client = None
test_case_generator = None
script_generator = None
document_processor = DocumentProcessor()

# Directories
UPLOAD_DIR = "data/uploads"
VECTOR_DB_DIR = "vector_db"
SCRIPTS_DIR = "tests/generated_scripts"

# Ensure directories exist - Fixed version
def create_directories():
    """Safely create all required directories"""
    directories = [UPLOAD_DIR, VECTOR_DB_DIR, SCRIPTS_DIR]
    for directory in directories:
        try:
            # Check if path exists and is a file (not a directory)
            if os.path.exists(directory) and os.path.isfile(directory):
                os.remove(directory)
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory {directory}: {e}")

# Create directories on module load
create_directories()

# Storage for uploaded files
uploaded_documents = []
uploaded_html_content = None
uploaded_html_path = None


# Pydantic models
class TestCaseRequest(BaseModel):
    query: str
    num_cases: Optional[int] = 10


class ScriptGenerationRequest(BaseModel):
    test_case: dict
    html_file_path: Optional[str] = "checkout.html"


class HealthResponse(BaseModel):
    status: str
    message: str


class KBStatusResponse(BaseModel):
    built: bool
    document_count: int
    sources: dict


# Helper function to initialize components
def initialize_components():
    """Initialize LLM client and generators"""
    global vector_store, llm_client, test_case_generator, script_generator
    
    try:
        # Initialize LLM client
        if llm_client is None:
            llm_client = get_groq_client()
        
        # Initialize vector store
        if vector_store is None:
            vector_store = VectorStore(index_path=VECTOR_DB_DIR)
            vector_store.load()  # Try to load existing index
        
        # Initialize generators
        if test_case_generator is None and vector_store and llm_client:
            test_case_generator = TestCaseGenerator(vector_store, llm_client)
        
        if script_generator is None and vector_store and llm_client:
            script_generator = ScriptGenerator(vector_store, llm_client)
        
        return True
    except Exception as e:
        print(f"Error initializing components: {str(e)}")
        return False


# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "message": "QA Agent API is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        if llm_client is None:
            initialize_components()
        
        # Test LLM connection
        is_connected = llm_client.test_connection() if llm_client else False
        
        if is_connected:
            return {
                "status": "healthy",
                "message": "All systems operational"
            }
        else:
            return {
                "status": "degraded",
                "message": "LLM connection issue"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload support documents"""
    global uploaded_documents
    
    try:
        uploaded_files = []
        
        for file in files:
            # Save file
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": file_path,
                "size": len(content)
            })
            
            # Store in memory
            uploaded_documents.append(file_path)
        
        return {
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} documents",
            "files": uploaded_files
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/upload-html")
async def upload_html(file: UploadFile = File(...)):
    """Upload HTML file (checkout.html)"""
    global uploaded_html_content, uploaded_html_path
    
    try:
        # Save HTML file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store content and path
        uploaded_html_content = content.decode('utf-8')
        uploaded_html_path = file_path
        
        # Also add to documents for processing
        uploaded_documents.append(file_path)
        
        return {
            "success": True,
            "message": "HTML file uploaded successfully",
            "filename": file.filename,
            "path": file_path,
            "size": len(content)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML upload failed: {str(e)}")


@app.post("/build-knowledge-base")
async def build_knowledge_base():
    """Process documents and build vector database"""
    global vector_store
    
    try:
        if not uploaded_documents:
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded. Please upload documents first."
            )
        
        # Initialize components
        initialize_components()
        
        # Process all documents
        all_chunks = []
        processed_files = []
        
        for doc_path in uploaded_documents:
            try:
                chunks = document_processor.process_and_chunk(doc_path)
                all_chunks.extend(chunks)
                processed_files.append(os.path.basename(doc_path))
                print(f"Processed: {os.path.basename(doc_path)} ({len(chunks)} chunks)")
            except Exception as e:
                print(f"Error processing {doc_path}: {str(e)}")
        
        if not all_chunks:
            raise HTTPException(
                status_code=500,
                detail="Failed to process any documents"
            )
        
        # Clear existing index and add new documents
        vector_store.clear()
        vector_store.add_documents(all_chunks)
        
        # Save index
        vector_store.save()
        
        # Get statistics
        stats = vector_store.get_stats()
        
        return {
            "success": True,
            "message": "Knowledge base built successfully",
            "processed_files": processed_files,
            "total_chunks": len(all_chunks),
            "statistics": stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge base build failed: {str(e)}")


@app.get("/knowledge-base-status", response_model=KBStatusResponse)
async def get_knowledge_base_status():
    """Get knowledge base status"""
    try:
        if vector_store is None:
            initialize_components()
        
        if vector_store is None:
            return {
                "built": False,
                "document_count": 0,
                "sources": {}
            }
        
        stats = vector_store.get_stats()
        
        return {
            "built": not stats['is_empty'],
            "document_count": stats['total_documents'],
            "sources": stats.get('sources', {})
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-test-cases")
async def generate_test_cases(request: TestCaseRequest):
    """Generate test cases based on query"""
    try:
        # Initialize components if needed
        if test_case_generator is None:
            initialize_components()
        
        if test_case_generator is None:
            raise HTTPException(
                status_code=400,
                detail="Knowledge base not built. Please build it first."
            )
        
        # Generate test cases
        test_cases = test_case_generator.generate_test_cases(
            user_query=request.query,
            html_content=uploaded_html_content,
            num_results=request.num_cases
        )
        
        return {
            "success": True,
            "query": request.query,
            "test_cases": test_cases,
            "count": len(test_cases)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test case generation failed: {str(e)}")


@app.post("/generate-script")
async def generate_script(request: ScriptGenerationRequest):
    """Generate Selenium script from test case"""
    try:
        # Initialize components if needed
        if script_generator is None:
            initialize_components()
        
        if script_generator is None:
            raise HTTPException(
                status_code=400,
                detail="Knowledge base not built. Please build it first."
            )
        
        if not uploaded_html_content:
            raise HTTPException(
                status_code=400,
                detail="HTML file not uploaded. Please upload checkout.html first."
            )
        
        # Generate script
        script = script_generator.generate_selenium_script(
            test_case=request.test_case,
            html_content=uploaded_html_content,
            html_file_path=request.html_file_path
        )
        
        # Save script
        test_id = request.test_case.get('test_id', 'TC-001').replace('-', '_')
        filename = f"test_{test_id.lower()}.py"
        filepath = script_generator.save_script(script, filename, SCRIPTS_DIR)
        
        return {
            "success": True,
            "test_id": request.test_case.get('test_id'),
            "script": script,
            "filepath": filepath,
            "filename": filename
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


@app.post("/clear-all")
async def clear_all():
    """Clear all uploaded files and knowledge base"""
    global uploaded_documents, uploaded_html_content, uploaded_html_path, vector_store
    
    try:
        # Clear uploads
        if os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
            os.makedirs(UPLOAD_DIR)
        
        # Clear vector store
        if vector_store:
            vector_store.clear()
            vector_store.save()
        
        # Reset variables
        uploaded_documents = []
        uploaded_html_content = None
        uploaded_html_path = None
        
        return {
            "success": True,
            "message": "All data cleared successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("QA Agent API starting up...")
    initialize_components()
    print("QA Agent API ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)