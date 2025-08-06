import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text(pdf_url):
    """Download PDF and extract ALL text from ALL pages"""
    try:
        response = requests.get(pdf_url, timeout=30)  # Increased timeout for larger files
        response.raise_for_status()
        
        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp.pdf")
        text = ""
        
        # Process ALL pages (removed page limit)
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            text += page_text + "\n"  # Add newline between pages
            
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

def smart_text_chunker(text, max_chunk_size=25000):
    """Smart chunking that handles large documents efficiently"""
    if len(text) <= max_chunk_size:
        return [text]
    
    # Split into chunks but try to keep sentences together
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        test_chunk = current_chunk + sentence + ". "
        if len(test_chunk) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
        else:
            current_chunk = test_chunk
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_large_document(pdf_text, questions):
    """Process large documents by finding relevant sections"""
    
    # Create keywords from questions for better section finding
    keywords = []
    for question in questions:
        # Extract important words from questions
        words = re.findall(r'\b\w{4,}\b', question.lower())
        keywords.extend(words)
    
    # Remove duplicates
    keywords = list(set(keywords))
    
    # Split document into paragraphs/sections
    paragraphs = [p.strip() for p in pdf_text.split('\n\n') if p.strip()]
    
    # Find relevant paragraphs that contain keywords
    relevant_sections = []
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        relevance_score = sum(1 for keyword in keywords if keyword in paragraph_lower)
        if relevance_score > 0:
            relevant_sections.append((paragraph, relevance_score))
    
    # Sort by relevance and take top sections
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    # Combine top relevant sections
    combined_text = ""
    for section, score in relevant_sections[:20]:  # Take top 20 relevant sections
        combined_text += section + "\n\n"
        if len(combined_text) > 20000:  # Limit total size
            break
    
    return combined_text if combined_text else pdf_text[:20000]

def extract_answers(doc_url, questions):
    """Extract answers from ENTIRE PDF"""
    try:
        # 1. Download and extract ALL text from ALL pages
        print("Downloading and extracting ALL pages...")
        pdf_text = download_and_extract_text(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        print(f"Extracted {len(pdf_text)} characters from PDF")

        # 2. Smart processing for large documents
        if len(pdf_text) > 25000:  # If document is large
            print("Large document detected, using smart processing...")
            processed_text = process_large_document(pdf_text, questions)
        else:
            processed_text = pdf_text

        # 3. Format questions
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        # 4. Create optimized prompt
        prompt = f"""You are a document expert. Answer these questions based ONLY on the document text below.

DOCUMENT TEXT:
{processed_text}

QUESTIONS:
{questions_text}

INSTRUCTIONS:
- Answer each question with specific information from the document
- Format as numbered list: 1. answer, 2. answer, etc.
- If not found, write "Not specified in document"
- Be concise but complete
- Use exact information from the document

ANSWERS:"""

        # 5. Single API call with fast model
        print("Sending to Gemini for analysis...")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistency
                max_output_tokens=3000,  # Increased for more detailed answers
            )
        )
        
        if not response or not response.text:
            return ["No response from AI model."] * len(questions)

        # 6. Parse responses
        print("Parsing responses...")
        answers = parse_fast_response(response.text.strip(), len(questions))
        return answers
        
    except Exception as e:
        print(f"Error in extract_answers: {e}")
        return [f"Error: {str(e)}"] * len(questions)

def parse_fast_response(text: str, expected_count: int) -> List[str]:
    """Fast parsing of numbered response"""
    answers = []
    
    # Quick regex for numbered answers
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches:
        # Extract answers in order
        for i in range(1, expected_count + 1):
            found = False
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    clean_answer = re.sub(r'\s+', ' ', answer_text.strip())
                    answers.append(clean_answer)
                    found = True
                    break
            if not found:
                answers.append("Not specified in document")
    else:
        # Simple fallback - split by lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:expected_count]:
            if '. ' in line:
                answer = line.split('. ', 1)[-1]
                answers.append(answer)
            else:
                answers.append(line)
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Not specified in document")
    
    return answers[:expected_count]

# ✅ Test function
if __name__ == "__main__":
    import time
    start_time = time.time()
    
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    questions = [
        "What is the grace period for premium payment?",
        "What is the waiting period for pre-existing diseases?",
        "Does this policy cover maternity expenses?"
    ]
    
    answers = extract_answers(url, questions)
    
    end_time = time.time()
    print(f"⏱️ Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")