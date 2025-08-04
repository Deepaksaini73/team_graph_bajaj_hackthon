# Document Q&A FastAPI Project

A FastAPI application that provides a REST API for document question-answering functionality.

## 📁 Project Structure

```
├── main.py              → FastAPI app with /ask endpoint
├── logic.py             → contains extract_answers() function
├── requirements.txt     → lists dependencies: fastapi, uvicorn, pydantic
└── README.md           → this file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

## 📋 API Documentation

### Endpoints

- **GET** `/` - Health check endpoint
- **POST** `/ask` - Extract answers from documents

### Interactive API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧠 API Usage

### POST /ask

Extract answers from documents based on provided questions.

**Request Body:**
```json
{
    "documents": "https://example.com/document.pdf",
    "questions": ["What is the main topic?", "Who is the author?"]
}
```

**Response:**
```json
{
    "answers": ["Dummy answer for: What is the main topic?", "Dummy answer for: Who is the author?"]
}
```

### Example using curl:

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": "https://example.com/sample.pdf",
       "questions": ["What is this document about?", "When was it published?"]
     }'
```

### Example using Python requests:

```python
import requests

url = "http://localhost:8000/ask"
data = {
    "documents": "https://example.com/sample.pdf",
    "questions": ["What is this document about?", "When was it published?"]
}

response = requests.post(url, json=data)
print(response.json())
```

## 🔧 Development

### Current Implementation

This is a starter template with dummy logic. The `extract_answers()` function in `logic.py` currently returns placeholder answers.

### Future Enhancements

To make this a production-ready Q&A system, you would need to implement:

1. **Document Processing:**
   - PDF text extraction (using libraries like PyPDF2, pdfplumber)
   - OCR for images (using Tesseract, pytesseract)
   - Document preprocessing and cleaning

2. **Question Answering:**
   - Transformer models (BERT, RoBERTa, DistilBERT)
   - Vector embeddings and similarity search
   - Named entity recognition
   - Contextual answer extraction

3. **Additional Features:**
   - File upload support
   - Caching mechanisms
   - Rate limiting
   - Authentication
   - Async document processing
   - Database integration

## 📦 Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation using Python type annotations

## 🛠️ Troubleshooting

If you encounter issues:

1. Ensure Python 3.7+ is installed
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `uvicorn main:app --reload`

## 📄 License

This project is open source and available under the [MIT License](LICENSE).