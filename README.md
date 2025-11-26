# 🤖 Autonomous QA Agent for Test Case and Script Generation

A complete AI-powered system that generates documentation-grounded test cases and executable Selenium scripts using RAG (Retrieval-Augmented Generation) and LLM.

## 🌟 Features

- **📚 Knowledge Base Ingestion**: Upload and process documents (MD, TXT, JSON, HTML)
- **🧪 Test Case Generation**: Generate documentation-grounded test cases using RAG
- **🎬 Selenium Script Generation**: Convert test cases to executable Python Selenium scripts
- **🔍 Semantic Search**: FAISS-based vector search for relevant documentation
- **⚡ Modern Stack**: FastAPI backend + Streamlit frontend
- **🎯 Strict Grounding**: No hallucinations - all test cases reference source documents

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Documents  │─────▶│  Vector DB   │◀────▶│  Groq LLM   │
│ (MD,TXT,HTML)│      │   (FAISS)    │      │  (llama-3.1)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────────────────────┐
                     │   RAG Pipeline              │
                     │   - Retrieval               │
                     │   - Context Building        │
                     │   - Generation              │
                     └──────────────────────────────┘
                            │
                            ▼
                     ┌──────────────────────────────┐
                     │   Test Cases & Scripts       │
                     └──────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.10 or higher
- Groq API key ([Get one here](https://console.groq.com))
- Chrome or Firefox browser (for Selenium)
- 4GB RAM minimum

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd qa-agent-project
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Setup Groq API

1. Sign up at [Groq Console](https://console.groq.com)
2. Generate an API key
3. Create `.env` file:

```bash
cp .env.example .env
```

4. Edit `.env` and add your API key:

```bash
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

### Step 5: Create Required Directories

```bash
mkdir -p data/sample_documents
mkdir -p data/uploads
mkdir -p vector_db
mkdir -p tests/generated_scripts
```

### Step 6: Add Sample Documents

Place these files in `data/sample_documents/`:
- `product_specs.md` - Product specifications and business rules
- `ui_ux_guide.txt` - UI/UX guidelines and validation rules
- `api_endpoints.json` - API documentation
- `checkout.html` - Functional checkout page

## 🎮 Usage

### Starting the Application

#### Terminal 1: Start Backend

```bash
# Activate virtual environment first
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

#### Terminal 2: Start Frontend

```bash
# Activate virtual environment first
streamlit run frontend/app.py --server.port 8501
```

Frontend will open automatically at: `http://localhost:8501`

### Using the Application

#### Step 1: Upload Documents

1. Open Streamlit interface at `http://localhost:8501`
2. Upload support documents (product_specs.md, ui_ux_guide.txt, api_endpoints.json)
3. Upload checkout.html
4. Click "Upload Documents" and "Upload HTML"

#### Step 2: Build Knowledge Base

1. Click "🚀 Build Knowledge Base" button
2. Wait for processing to complete (~ 30-60 seconds)
3. Verify success message shows document count

#### Step 3: Generate Test Cases

1. Enter a query like:
   - "Generate test cases for discount code feature"
   - "Generate test cases for form validation"
   - "Generate test cases for shopping cart"
2. Or click a suggested query button
3. Adjust number of test cases (1-15)
4. Click "🎯 Generate Test Cases"
5. Review generated test cases in expandable cards

#### Step 4: Generate Selenium Scripts

1. Select a test case by clicking "Generate Script 📝"
2. Update HTML file path if needed
3. Click "⚡ Generate Selenium Script"
4. Review generated script
5. Download script using "📥 Download Script" button

#### Step 5: Run Generated Scripts

1. Save the downloaded script (e.g., `test_tc_001.py`)
2. Update the HTML file path in the script:
   ```python
   self.driver.get("file:///path/to/checkout.html")
   ```
3. Install Selenium if not already installed:
   ```bash
   pip install selenium
   ```
4. Install ChromeDriver or GeckoDriver
5. Run the script:
   ```bash
   python test_tc_001.py
   ```

## 📂 Project Structure

```
qa-agent-project/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── groq_client.py             # Groq API client
│   ├── document_processor.py      # Document parsing
│   ├── vector_store.py            # FAISS vector database
│   ├── test_case_generator.py     # RAG + LLM for test cases
│   └── script_generator.py        # Selenium script generation
├── frontend/
│   └── app.py                     # Streamlit UI
├── data/
│   ├── sample_documents/          # Sample support docs
│   │   ├── product_specs.md
│   │   ├── ui_ux_guide.txt
│   │   └── api_endpoints.json
│   ├── uploads/                   # Uploaded files (gitignored)
│   └── checkout.html
├── tests/
│   └── generated_scripts/         # Generated Selenium scripts
├── vector_db/                     # FAISS index (gitignored)
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── .env                          # Your API keys (gitignored)
```

## 📚 Support Documents Included

### 1. product_specs.md
Product specifications including:
- Discount codes (SAVE15, SAVE20, FLAT50)
- Shipping rules (Standard, Express)
- Pricing and tax calculations
- Payment methods
- Validation rules
- Product inventory

### 2. ui_ux_guide.txt
UI/UX guidelines covering:
- Form validation rules
- Button styling and states
- Cart display requirements
- Discount code handling
- Order summary layout
- Accessibility requirements
- Responsive design

### 3. api_endpoints.json
API documentation for:
- Cart operations (add, remove, update)
- Discount code validation
- Order submission
- Shipping calculation
- Product listing

### 4. checkout.html
Functional e-commerce checkout page with:
- 5 products with prices
- Shopping cart with quantity controls
- Discount code application
- Customer information form
- Shipping method selection
- Payment method selection
- Order validation and submission

## 🎯 Sample Test Scenarios

The system can generate test cases for:

### Discount Code Feature
- Apply valid discount codes (SAVE15, SAVE20, FLAT50)
- Handle invalid discount codes
- Verify minimum order requirements
- Calculate discount correctly

### Form Validation
- Required field validation
- Email format validation
- Terms and conditions acceptance
- Real-time validation feedback

### Shopping Cart
- Add/remove items
- Update quantities
- Calculate totals correctly
- Empty cart handling

### Payment Methods
- Credit card selection
- PayPal selection
- Cash on Delivery restrictions
- Payment method validation

### Checkout Process
- Minimum order validation
- Shipping cost calculation
- Tax calculation
- Order submission

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI |
| **Frontend Framework** | Streamlit |
| **LLM Provider** | Groq (llama-3.1-70b-versatile) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Vector Database** | FAISS |
| **Document Processing** | BeautifulSoup4 |
| **Test Automation** | Selenium WebDriver |
| **HTTP Client** | Requests |

## 🐛 Troubleshooting

### Issue: "Groq API key not provided"

**Solution:** 
1. Make sure `.env` file exists
2. Verify `GROQ_API_KEY` is set correctly
3. Restart the backend server

### Issue: "Connection refused" when accessing API

**Solution:**
1. Make sure backend is running: `http://localhost:8000`
2. Check if port 8000 is available
3. Try: `curl http://localhost:8000/health`

### Issue: "Knowledge base not built"

**Solution:**
1. Upload documents first
2. Click "Build Knowledge Base" button
3. Wait for processing to complete
4. Check sidebar status shows "Knowledge Base Ready"

### Issue: "No relevant documentation found"

**Solution:**
1. Rebuild knowledge base
2. Try more specific queries
3. Ensure documents contain relevant information
4. Check vector_db directory exists and has data

### Issue: Selenium script fails to run

**Solution:**
1. Update HTML file path in script
2. Install ChromeDriver: `brew install chromedriver` (Mac) or download from [ChromeDriver](https://chromedriver.chromium.org/)
3. Make sure Chrome browser is installed
4. Check Selenium version: `pip show selenium`

### Issue: Script generation takes too long

**Solution:**
1. Check Groq API status
2. Reduce number of test cases
3. Simplify test case complexity
4. Check internet connection

## 📊 API Endpoints

The backend exposes these REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/upload-documents` | POST | Upload support documents |
| `/upload-html` | POST | Upload HTML file |
| `/build-knowledge-base` | POST | Process documents and build vector DB |
| `/knowledge-base-status` | GET | Check KB status |
| `/generate-test-cases` | POST | Generate test cases |
| `/generate-script` | POST | Generate Selenium script |
| `/clear-all` | POST | Clear all data |

## 🧪 Testing the System

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Check KB status
curl http://localhost:8000/knowledge-base-status
```

### Test Frontend

1. Open `http://localhost:8501`
2. Verify all sections load
3. Upload sample documents
4. Build knowledge base
5. Generate test cases
6. Generate script



- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Groq Documentation](https://console.groq.com/docs)
- [FAISS Documentation](https://faiss.ai/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)

---

**Built with ❤️ using FastAPI, Streamlit, Groq, and FAISS**

