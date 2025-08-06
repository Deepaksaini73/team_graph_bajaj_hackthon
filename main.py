from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from logic import extract_answers
from logic_v2 import extract_answers_v2  # Import V2 function
import os

app = FastAPI(title="Document Q&A API", version="2.0.0")
security = HTTPBearer()

# Your team's auth token
VALID_TOKEN = "20c8eab302ed3ef3e0178c0e233611b785f20941c23c4343fbc5bbea9de4e3ea"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

class QuestionRequest(BaseModel):
    documents: str
    questions: List[str]

class QuestionResponse(BaseModel):
    answers: List[str]

@app.get("/")
async def root():
    return {"message": "Document Q&A API v2.0 - Use /api/v1/hackrx/run (basic) or /api/v2/hackrx/run (enhanced)"}

@app.post("/api/v1/hackrx/run", response_model=QuestionResponse)
async def ask_questions_v1(request: QuestionRequest, token: str = Depends(verify_token)):
    """V1 Basic document Q&A"""
    answers = extract_answers(request.documents, request.questions)
    return QuestionResponse(answers=answers)

@app.post("/api/v2/hackrx/run", response_model=QuestionResponse)
async def ask_questions_v2(request: QuestionRequest, token: str = Depends(verify_token)):
    """
    V2 Enhanced lightweight document Q&A
    
    Improvements:
    - Smart keyword-based section extraction
    - Enhanced prompting for insurance documents
    - Better response parsing
    - Page-aware processing
    - Optimized for Render deployment (<512MB)
    """
    answers = extract_answers_v2(request.documents, request.questions)
    return QuestionResponse(answers=answers)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
