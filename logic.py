import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text(pdf_url):
    """Download PDF and extract text"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp.pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # Clean up temp file
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")
            
        return text
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")
        raise e

def chunk_text_simple(text, max_chunk_size=8000):
    """Simple text chunking by character count"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    words = text.split()
    current_chunk = ""
    
    for word in words:
        test_chunk = current_chunk + " " + word if current_chunk else word
        if len(test_chunk) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            current_chunk = test_chunk
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def ask_gemini_simple(questions_text, document_text):
    """Simple Gemini call without vector search"""
    prompt = f"""You are a helpful document assistant. Answer the following questions based ONLY on the provided document text.

DOCUMENT TEXT:
{document_text}

QUESTIONS:
{questions_text}

INSTRUCTIONS:
- Answer each question based strictly on the document text above
- Format your response as a numbered list (1., 2., 3., etc.)
- If information is not found, respond with "Information not found in document"
- Keep answers concise and accurate

ANSWERS:"""

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error calling Gemini: {str(e)}"

def parse_numbered_response(text: str, expected_count: int) -> List[str]:
    """Parse numbered response from Gemini"""
    answers = []
    
    # Try to find numbered answers (1., 2., 3., etc.)
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches:
        # Sort by number and extract answers
        sorted_matches = sorted(matches, key=lambda x: int(x[0]))
        for match in sorted_matches:
            answer = match[1].strip()
            # Clean up the answer
            answer = re.sub(r'\n+', ' ', answer)
            answer = re.sub(r'\s+', ' ', answer)
            answers.append(answer)
    else:
        # Fallback: try to split by lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answer = ""
        
        for line in lines:
            if re.match(r'^\d+\.', line):
                if current_answer:
                    answers.append(current_answer.strip())
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line if current_answer else line
        
        if current_answer:
            answers.append(current_answer.strip())
    
    # Ensure we have the right number of answers
    while len(answers) < expected_count:
        answers.append("Information not found in document")
    
    return answers[:expected_count]

def extract_answers(doc_url, questions):
    """Simple function to extract answers from PDF"""
    try:
        # 1. Download and extract text
        pdf_text = download_and_extract_text(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        # 2. Format questions
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        # 3. If document is too large, process in chunks
        chunks = chunk_text_simple(pdf_text, 8000)
        
        if len(chunks) == 1:
            # Small document - process all at once
            response_text = ask_gemini_simple(questions_text, chunks[0])
            answers = parse_numbered_response(response_text, len(questions))
        else:
            # Large document - process chunks and combine results
            all_answers = []
            for i, chunk in enumerate(chunks):
                chunk_response = ask_gemini_simple(questions_text, chunk)
                chunk_answers = parse_numbered_response(chunk_response, len(questions))
                all_answers.append(chunk_answers)
            
            # Combine answers from all chunks
            final_answers = []
            for q_idx in range(len(questions)):
                best_answer = "Information not found in document"
                for chunk_answers in all_answers:
                    if (q_idx < len(chunk_answers) and 
                        chunk_answers[q_idx] != "Information not found in document" and
                        len(chunk_answers[q_idx]) > len(best_answer)):
                        best_answer = chunk_answers[q_idx]
                final_answers.append(best_answer)
            
            answers = final_answers
        
        return answers
        
    except Exception as e:
        return [f"Error: {str(e)}"] * len(questions)

# ✅ Test function
if __name__ == "__main__":
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    questions = [
        "What is the grace period for premium payment?",
        "What is the waiting period for pre-existing diseases?",
        "Does this policy cover maternity expenses?"
    ]
    answers = extract_answers(url, questions)
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")