from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from logic import extract_answers
import os

app = FastAPI(title="Document Q&A API", version="1.0.0")
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
    return {"message": "Document Q&A API is running!"}

@app.post("/api/v1/hackrx/run", response_model=QuestionResponse)
async def ask_questions(request: QuestionRequest, token: str = Depends(verify_token)):
    """
    Extract answers from documents based on provided questions
    
    Headers required:
    - Authorization: Bearer 20c8eab302ed3ef3e0178c0e233611b785f20941c23c4343fbc5bbea9de4e3ea
    
    Body:
    - **documents**: URL to PDF document
    - **questions**: List of questions to answer
    """
    answers = extract_answers(request.documents, request.questions)
    return QuestionResponse(answers=answers)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
