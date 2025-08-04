from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from logic import extract_answers
import os

app = FastAPI(title="Document Q&A API", version="1.0.0")

class QuestionRequest(BaseModel):
    documents: str
    questions: List[str]

class QuestionResponse(BaseModel):
    answers: List[str]

@app.get("/")
async def root():
    return {"message": "Document Q&A API is running!"}

@app.post("/api/v1/hackrx/run", response_model=QuestionResponse)
async def ask_questions(request: QuestionRequest):
    """
    Extract answers from documents based on provided questions
    
    - **documents**: URL or path to PDF or image document
    - **questions**: List of questions to answer
    """
    answers = extract_answers(request.documents, request.questions)
    return QuestionResponse(answers=answers)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
