import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyBX7vw2ZiEju7qt1fRiP6HDYsxgGtvVycI")

# Use the free tier model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def download_and_extract_text(pdf_url):
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

def extract_answers(doc_url, questions):
    try:
        # 1. Download and extract text from PDF
        pdf_text = download_and_extract_text(doc_url)

        # 2. Create prompt for Gemini
        prompt = f"""
You are a helpful assistant. Below is the content of a medical insurance policy PDF.
Answer the following questions based only on the content of this document.
Please provide answers in a numbered list format (1., 2., 3., etc.).

--- DOCUMENT START ---
{pdf_text}
--- DOCUMENT END ---

Questions:
"""

        for idx, q in enumerate(questions, 1):
            prompt += f"{idx}. {q}\n"
        
        prompt += "\nPlease answer each question clearly and concisely, numbered 1., 2., 3., etc."

        # 3. Send to Gemini with error handling
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return ["No response from AI model."] * len(questions)

        # 4. Parse the response more robustly
        text = response.text.strip()
        answers = parse_numbered_response(text, len(questions))

        return answers
        
    except Exception as e:
        print(f"Error in extract_answers: {e}")
        return [f"Error: {str(e)}"] * len(questions)

def parse_numbered_response(text: str, expected_count: int) -> List[str]:
    """Parse numbered response from Gemini"""
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
                "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
    answers = extract_answers(url, questions)
    for q, a in zip(questions, answers):
        print(f"\nQ: {q}\nA: {a}")