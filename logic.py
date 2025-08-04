import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyBX7vw2ZiEju7qt1fRiP6HDYsxgGtvVycI")

# Initialize the sentence transformer model globally
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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

def chunk_text(text, chunk_size=150):
    """Split text into chunks for better retrieval"""
    sentences = text.split(". ")
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def embed_chunks(chunks, model):
    """Create embeddings for text chunks"""
    return model.encode(chunks)

def create_faiss_index(embeddings):
    """Create FAISS index for similarity search"""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def retrieve_chunks(question, chunks, index, model, top_k=3):
    """Retrieve most relevant chunks for a question"""
    q_embed = model.encode([question])
    distances, indices = index.search(np.array(q_embed), top_k)
    return [chunks[i] for i in indices[0]]

def ask_gemini(question, context_chunks):
    """Ask Gemini with relevant context chunks"""
    context = "\n\n".join(context_chunks)
    prompt = f"""
You are a policy assistant. Answer based ONLY on the following extracted clauses.

Clauses:
{context}

Question: {question}
Answer:"""

    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = model.generate_content(prompt)
    return response.text.strip()

def extract_answers(doc_url, questions):
    """Main function to extract answers using RAG approach"""
    try:
        # 1. Download and extract text from PDF
        print("Downloading and extracting PDF text...")
        pdf_text = download_and_extract_text(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        # 2. Chunk the text for better retrieval
        print("Chunking text...")
        chunks = chunk_text(pdf_text)
        
        if not chunks:
            return ["No valid chunks found in document."] * len(questions)

        # 3. Create embeddings and FAISS index
        print("Creating embeddings and index...")
        embeddings = embed_chunks(chunks, embedding_model)
        index = create_faiss_index(np.array(embeddings))

        # 4. Answer each question using RAG
        print("Answering questions with Gemini...")
        answers = []
        for question in questions:
            try:
                # Retrieve relevant chunks
                relevant_chunks = retrieve_chunks(question, chunks, index, embedding_model)
                
                # Get answer from Gemini
                answer = ask_gemini(question, relevant_chunks)
                answers.append(answer)
                
            except Exception as e:
                print(f"Error answering question '{question}': {e}")
                answers.append(f"Error processing question: {str(e)}")

        return answers
        
    except Exception as e:
        print(f"Error in extract_answers: {e}")
        return [f"Error: {str(e)}"] * len(questions)

def parse_numbered_response(text: str, expected_count: int) -> List[str]:
    """Parse numbered response from Gemini (kept for compatibility)"""
    answers = []
    
    # Try to find numbered answers (1., 2., 3., etc.)
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches:
        # Sort by number and extract answers
        sorted_matches = sorted(matches, key=lambda x: int(x[0]))
        answers = [match[1].strip() for match in sorted_matches]
    else:
        # Fallback: split by lines and clean
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if '. ' in line and line[0].isdigit():
                # Extract answer after number
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    answers.append(parts[1].strip())
            elif line and not line[0].isdigit():
                # Line without number, might be continuation
                if answers:
                    answers[-1] += ' ' + line
                else:
                    answers.append(line)
    
    # Ensure we have the right number of answers
    while len(answers) < expected_count:
        answers.append("No answer found.")
    
    return answers[:expected_count]


# ✅ Run this to test
if __name__ == "__main__":
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    questions = [
                "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
                "What is the waiting period for pre-existing diseases (PED) to be covered?",
                "Does this policy cover maternity expenses, and what are the conditions?",
                "What is the waiting period for cataract surgery?",
                "Are the medical expenses for an organ donor covered under this policy?",
                "What is the No Claim Discount (NCD) offered in this policy?",
                "Is there a benefit for preventive health check-ups?",
                "How does the policy define a 'Hospital'?",
                "What is the extent of coverage for AYUSH treatments?",
                "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
    answers = extract_answers(url, questions)
    for q, a in zip(questions, answers):
        print(f"\nQ: {q}\nA: {a}")