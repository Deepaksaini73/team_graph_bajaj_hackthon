# Document Q&A FastAPI Project

A FastAPI application that provides a REST API for document question-answering functionality using Google's Gemini AI to extract answers from PDF documents.

## 📁 Project Structure

```
├── main.py              → FastAPI app with /api/v1/hackrx/run endpoint
├── logic.py             → contains extract_answers() function with Gemini AI integration
├── requirements.txt     → lists dependencies: fastapi, uvicorn, google-generativeai, PyMuPDF, requests, pydantic
└── README.md           → this file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

Edit `logic.py` and replace the API key:
```python
genai.configure(api_key="YOUR_GEMINI_API_KEY_HERE")
```

### 3. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

## 📋 API Documentation

### Endpoints

- **GET** `/` - Health check endpoint
- **POST** `/api/v1/hackrx/run` - Extract answers from PDF documents using Gemini AI

### Interactive API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧠 API Usage

### POST /api/v1/hackrx/run

Extract answers from PDF documents based on provided questions using Google Gemini AI.

**Request Body:**
```json
{
    "documents": "https://example.com/document.pdf",
    "questions": ["What is the grace period for premium payment?", "What is the waiting period for pre-existing diseases?"]
}
```

**Response:**
```json
{
    "answers": ["The grace period is 30 days from the due date.", "The waiting period for PED is 48 months."]
}
```

### Example using curl:

```bash
curl -X POST "http://localhost:8000/api/v1/hackrx/run" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
       "questions": ["What is the grace period for premium payment?", "What is the waiting period for pre-existing diseases?"]
     }'
```

### Example using Python requests:

```python
import requests

url = "http://localhost:8000/api/v1/hackrx/run"
data = {
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?"
    ]
}

response = requests.post(url, json=data)
print(response.json())
```

## 🔧 Technical Implementation

### Current Features

- **PDF Processing**: Downloads and extracts text from PDF URLs using PyMuPDF (fitz)
- **AI Integration**: Uses Google Gemini 2.0 Flash Exp model for question answering
- **Response Parsing**: Intelligent parsing of numbered responses from AI model
- **Error Handling**: Comprehensive error handling for network, file, and API issues
- **Temporary File Management**: Automatic cleanup of downloaded PDF files

### How It Works

1. **Document Processing**: Downloads PDF from provided URL and extracts text using PyMuPDF
2. **AI Processing**: Sends document text and questions to Google Gemini AI model
3. **Response Parsing**: Parses AI response using regex patterns to extract numbered answers
4. **Error Handling**: Returns meaningful error messages if processing fails

### Model Configuration

Currently using Google's free tier model:
- Model: `gemini-2.0-flash-exp`
- Provider: Google Generative AI
- Authentication: API Key based

## 📦 Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation using Python type annotations
- **google-generativeai**: Google's Gemini AI SDK
- **PyMuPDF**: PDF text extraction library
- **requests**: HTTP library for downloading PDFs

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Error**: Ensure you have a valid Gemini API key configured in `logic.py`
2. **PDF Download Issues**: Check if the PDF URL is accessible and valid
3. **Model Limits**: Free tier has rate limits - wait between requests if you get quota errors

### Setup Issues

If you encounter issues:

1. Ensure Python 3.7+ is installed
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure your Gemini API key in `logic.py`
6. Run the app: `uvicorn main:app --reload`

### Testing the Logic

You can test the core functionality directly:

```bash
python logic.py
```

This will run the test case with the provided insurance policy PDF and sample questions.

## 🔐 Security Notes

- **API Key**: Never commit your actual Gemini API key to version control
- **Input Validation**: The API validates input using Pydantic models
- **File Cleanup**: Temporary PDF files are automatically cleaned up after processing

## 📄 License

This project is open source and available under the [MIT License](LICENSE).