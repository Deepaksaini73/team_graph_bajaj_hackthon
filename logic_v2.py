import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List
import json

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text_v2(pdf_url):
    """Download PDF and extract ALL text from ALL pages - V2"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with open("temp_v2.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp_v2.pdf")
        text = ""
        
        # Process ALL pages with page metadata
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            # Add page markers for better context
            text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            
        doc.close()
        
        # Clean up temp file
        if os.path.exists("temp_v2.pdf"):
            os.remove("temp_v2.pdf")
            
        return text
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists("temp_v2.pdf"):
            os.remove("temp_v2.pdf")
        raise e

def lightweight_chunker_v2(text, max_chunk_size=8000):
    """Lightweight text chunking optimized for insurance documents"""
    if len(text) <= max_chunk_size:
        return [text]
    
    # Split by common insurance document sections
    section_patterns = [
        r'\n--- PAGE \d+ ---\n',  # Page breaks
        r'\n\d+\.\s+[A-Z][^.]+\n',  # Numbered sections
        r'\n[A-Z][A-Z\s]+:\n',  # ALL CAPS headers
        r'\n\n'  # Double newlines
    ]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
        
        if len(test_chunk) <= max_chunk_size:
            current_chunk = test_chunk
        else:
            # Save current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def enhanced_prompt_with_citations_v2(questions_text, processed_text):
    """Create enhanced prompt with citation requirements - UNIVERSAL VERSION"""
    return f"""DOCUMENT ANALYSIS EXPERT WITH SOURCE CITATIONS

You are analyzing a document to answer questions accurately. For each question, provide the answer AND cite the exact text from the document that supports your answer.

DOCUMENT CONTENT:
{processed_text}

QUESTIONS TO ANSWER:
{questions_text}

ANALYSIS RULES:
- Extract EXACT information from the document (numbers, dates, percentages, amounts, time periods)
- For any waiting periods or grace periods: State exact duration
- For coverage or benefits: Include specific conditions and limits  
- For definitions or terms: Use exact document language
- Be precise with numerical values and technical terms

RESPONSE FORMAT FOR EACH ANSWER:
1. [Direct Answer based on document]
   📋 Source: "[Exact text from document that supports this answer]"

2. [Direct Answer based on document]
   📋 Source: "[Exact text from document that supports this answer]"

CRITICAL REQUIREMENTS:
- Always include the 📋 Source citation with exact text from the document
- If information is unclear or missing, state "Information not clearly specified in document"
- Quote the EXACT sentence or phrase from the document
- Make sure the source text directly supports your answer
- Do not make assumptions - only use information explicitly stated in the document

ANSWERS WITH EXACT CITATIONS:"""

def safe_gemini_call_v2(prompt):
    """Safe Gemini API call with better error handling"""
    try:
        # Use reliable free model
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,  # Maximum consistency
                max_output_tokens=3000,  # Increased for citations
                top_p=0.8,
                top_k=20
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )
        
        # Safe response extraction
        if response and response.text:
            return response.text.strip()
        elif response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text.strip()
        
        return "Unable to generate response from AI model"
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return f"AI model error: {str(e)}"

def extract_answers_v2(doc_url, questions):
    """Enhanced lightweight answer extraction for V2 with citations - UNIVERSAL"""
    try:
        print("🚀 Starting V2 enhanced extraction with citations...")
        
        # Step 1: Download and extract with page markers
        print("📄 Downloading and extracting PDF with page context...")
        pdf_text = download_and_extract_text_v2(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        print(f"📊 Extracted {len(pdf_text)} characters from PDF")

        # Step 2: Smart processing based on document size
        if len(pdf_text) > 25000:
            print("🧠 Large document - using smart keyword-based extraction...")
            processed_text = smart_keyword_search_v2(pdf_text, questions)
        else:
            print("📋 Small document - using full content...")
            processed_text = pdf_text

        print(f"🔍 Processing {len(processed_text)} characters of relevant content")

        # Step 3: Format questions for better processing
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        # Step 4: Create enhanced UNIVERSAL prompt with citations
        prompt = enhanced_prompt_with_citations_v2(questions_text, processed_text)
        
        # Step 5: Single optimized API call
        print("🤖 Sending to Gemini for enhanced document analysis with citations...")
        response_text = safe_gemini_call_v2(prompt)
        
        if "error" in response_text.lower():
            return [response_text] * len(questions)

        # Step 6: Parse with improved parsing including citations
        print("📝 Parsing enhanced responses with citations...")
        answers = parse_enhanced_response_with_citations_v2(response_text, len(questions))
        
        print("✅ V2 extraction with citations completed successfully")
        return answers
        
    except Exception as e:
        print(f"❌ Error in V2 extract_answers: {e}")
        return [f"V2 Error: {str(e)}"] * len(questions)

def smart_keyword_search_v2(text, questions):
    """Universal keyword-based relevant section finder for any document type"""
    # Extract keywords from questions
    all_keywords = []
    for question in questions:
        # Extract meaningful words (3+ chars for better coverage)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
    
    # Remove duplicates and common words (expanded stop words)
    stop_words = {
        'what', 'when', 'where', 'does', 'this', 'policy', 'under', 'with', 
        'from', 'that', 'have', 'will', 'can', 'are', 'the', 'and', 'for',
        'how', 'why', 'who', 'which', 'any', 'all', 'some', 'may', 'must'
    }
    keywords = list(set(word for word in all_keywords if word not in stop_words))
    
    # Split text into sections (works for any document type)
    sections = text.split('\n--- PAGE')
    relevant_sections = []
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        # Calculate relevance score based on keyword matches
        relevance = sum(1 for keyword in keywords if keyword in section_lower)
        
        # Bonus points for sections with multiple keyword matches
        if relevance > 2:
            relevance += 1
            
        if relevance > 0:
            relevant_sections.append((section, relevance))
    
    # Sort by relevance and combine top sections
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    combined_text = ""
    for section, score in relevant_sections[:20]:  # Top 20 sections for better coverage
        combined_text += section + "\n"
        if len(combined_text) > 25000:  # Increased limit for better context
            break
    
    return combined_text if combined_text else text[:25000]

def parse_enhanced_response_with_citations_v2(text: str, expected_count: int) -> List[str]:
    """Enhanced response parsing with citation extraction"""
    answers = []
    
    # Strategy 1: Parse numbered answers with citations
    # Look for pattern: 1. [answer] 📋 Source: "[citation]"
    pattern = r'(\d+)\.\s*(.+?)(?=📋\s*Source:|$)'
    citation_pattern = r'📋\s*Source:\s*"([^"]+)"'
    
    # Split by numbered sections
    sections = re.split(r'(?=\d+\.)', text)
    
    for section in sections:
        if not section.strip():
            continue
            
        # Extract number
        num_match = re.match(r'^(\d+)\.', section.strip())
        if not num_match:
            continue
            
        num = int(num_match.group(1))
        if num > expected_count:
            continue
        
        # Extract answer part (before citation)
        answer_text = section.strip()
        
        # Look for citation
        citation_match = re.search(citation_pattern, answer_text)
        citation = ""
        if citation_match:
            citation = citation_match.group(1)
            # Remove citation from answer text
            answer_text = re.sub(r'📋\s*Source:\s*"[^"]+"', '', answer_text)
        
        # Clean up answer
        answer_text = re.sub(r'^\d+\.\s*', '', answer_text).strip()
        answer_text = re.sub(r'\s+', ' ', answer_text)
        
        # Combine answer with citation if found
        if citation:
            final_answer = f"{answer_text}\n📋 Source: \"{citation}\""
        else:
            final_answer = answer_text
        
        # Ensure we have the right position
        while len(answers) < num - 1:
            answers.append("Information not clearly specified in document")
        
        if len(answers) == num - 1:
            answers.append(final_answer)
    
    # Strategy 2: Fallback parsing if citations not properly formatted
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answers = []
        current_answer = ""
        
        for line in lines:
            if re.match(r'^\d+\.', line):
                # Save previous answer
                if current_answer:
                    current_answers.append(current_answer.strip())
                # Start new answer
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                # Continuation of current answer
                current_answer += " " + line
        
        # Add last answer
        if current_answer:
            current_answers.append(current_answer.strip())
        
        # Use fallback answers to fill gaps
        while len(answers) < expected_count and len(current_answers) > len(answers):
            answers.append(current_answers[len(answers)])
    
    # Ensure we have exact count
    while len(answers) < expected_count:
        answers.append("Information not clearly specified in document")
    
    return answers[:expected_count]

# ✅ Test function for V2 with citations
if __name__ == "__main__":
    import time
    start_time = time.time()
    
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    questions = [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?"
    ]
    
    print("🧪 Testing V2 Logic with Citations...")
    answers = extract_answers_v2(url, questions)
    
    end_time = time.time()
    print(f"\n⏱️ V2 Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")
        print("---" * 20)