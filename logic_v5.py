import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
import json
import time
from typing import List, Dict, Any

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text_v5(pdf_url):
    """V5: Fast PDF extraction with V3-style cleaning"""
    try:
        response = requests.get(pdf_url, timeout=20)  # Balanced timeout
        response.raise_for_status()
        
        with open("temp_v5.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp_v5.pdf")
        text = ""
        
        # Process ALL pages like V3 but faster
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            
            # V3-style text cleaning for accuracy
            page_text = clean_extracted_text_v5(page_text)
            
            # V3-style page markers
            text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            
        doc.close()
        
        if os.path.exists("temp_v5.pdf"):
            os.remove("temp_v5.pdf")
            
        return text
    except Exception as e:
        if os.path.exists("temp_v5.pdf"):
            os.remove("temp_v5.pdf")
        raise e

def clean_extracted_text_v5(text):
    """V5: Advanced text cleaning like V3 for better accuracy"""
    # Fix common OCR errors (from V3)
    text = re.sub(r'\bO\b(?=\d)', '0', text)  # O to 0 in numbers
    text = re.sub(r'\bl\b(?=\d)', '1', text)  # l to 1 in numbers
    
    # Normalize currency symbols (from V3)
    text = re.sub(r'\bRs\.?\s*', '₹', text)
    text = re.sub(r'\bINR\s*', '₹', text)
    
    # Fix spacing issues (from V3)
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean paragraph breaks
    
    # Fix common formatting issues (from V3)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)  # Fix percentage spacing
    text = re.sub(r'(\d+)\s*₹', r'₹\1', text)  # Fix currency spacing
    
    return text.strip()

def enhanced_keyword_search_v5(text, questions):
    """V5: Enhanced keyword search based on V3 but optimized for speed"""
    # Extract keywords like V3
    all_keywords = []
    for question in questions:
        # Extract meaningful words (3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
        
        # Extract abbreviations and important terms
        abbrevs = re.findall(r'\b[A-Z]{2,}\b', question)  # PED, ICU, etc.
        all_keywords.extend([abbrev.lower() for abbrev in abbrevs])
    
    # V3-style enhanced stop words
    stop_words = {
        'what', 'when', 'where', 'does', 'this', 'policy', 'under', 'with', 
        'from', 'that', 'have', 'will', 'can', 'are', 'the', 'and', 'for',
        'how', 'why', 'who', 'which', 'any', 'all', 'some', 'may', 'must',
        'not', 'but', 'his', 'her', 'you', 'your', 'our', 'their'
    }
    
    # V3-style domain-specific terms with higher weights
    domain_terms = {
        'insurance': ['premium', 'coverage', 'deductible', 'claim', 'benefit', 'exclusion', 'rider'],
        'medical': ['treatment', 'hospital', 'surgery', 'diagnosis', 'therapy', 'doctor', 'patient'],
        'financial': ['amount', 'limit', 'payment', 'cost', 'fee', 'charge', 'expense'],
        'time': ['period', 'waiting', 'grace', 'duration', 'months', 'years', 'days'],
        'legal': ['terms', 'conditions', 'clause', 'section', 'provision']
    }
    
    keywords = list(set(word for word in all_keywords if word not in stop_words))
    
    # V3-style section processing
    sections = text.split('\n--- PAGE')
    relevant_sections = []
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        relevance = 0
        
        # Basic keyword matches (like V3)
        for keyword in keywords:
            if keyword in section_lower:
                relevance += 1
        
        # Domain-specific term matching with higher weight (like V3)
        for category, terms in domain_terms.items():
            for term in terms:
                if term in section_lower:
                    relevance += 2  # Higher weight for domain terms
        
        # V3-style bonuses
        if relevance > 3:
            relevance += 2
            
        # Numerical data bonus (like V3)
        if re.search(r'\d+\s*(%|months?|years?|days?|₹)', section_lower):
            relevance += 1
            
        if relevance > 0:
            relevant_sections.append((section, relevance))
    
    # V3-style sorting and combining
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    combined_text = ""
    for section, score in relevant_sections[:20]:  # Balanced section count
        combined_text += section + "\n"
        if len(combined_text) > 25000:  # Balanced text size
            break
    
    return combined_text if combined_text else text[:25000]

def preprocess_questions_v5(questions):
    """V5: V3-style question preprocessing"""
    processed_questions = []
    
    # V3-style abbreviation expansions
    abbreviations = {
        'PED': 'Pre-existing diseases',
        'ICU': 'Intensive Care Unit',
        'OPD': 'Outpatient Department',
        'IPD': 'Inpatient Department',
        'EMI': 'Equated Monthly Installment',
        'GST': 'Goods and Services Tax',
        'TPA': 'Third Party Administrator'
    }
    
    for question in questions:
        # Expand abbreviations (like V3)
        processed_question = question
        for abbrev, expansion in abbreviations.items():
            processed_question = re.sub(rf'\b{abbrev}\b', expansion, processed_question, flags=re.IGNORECASE)
        
        # V3-style context enhancement
        if 'grace period' in processed_question.lower() and 'premium' not in processed_question.lower():
            processed_question = processed_question.replace('grace period', 'grace period for premium payments')
        
        if 'waiting period' in processed_question.lower() and 'disease' not in processed_question.lower():
            processed_question = processed_question.replace('waiting period', 'waiting period for diseases or conditions')
        
        processed_questions.append(processed_question)
    
    return processed_questions

def enhanced_prompt_v5(questions_text, processed_text):
    """V5: Enhanced prompt based on V3 but optimized for simple answers"""
    return f"""EXPERT DOCUMENT ANALYZER - SIMPLE ACCURATE ANSWERS

You are an expert document analyst. Analyze the document and provide precise, simple answers.

DOCUMENT CONTENT:
{processed_text}

QUESTIONS TO ANALYZE:
{questions_text}

ANSWER REQUIREMENTS:
- Extract EXACT numerical values with units (30 days, 36 months, 2 years, 5%, ₹10,000)
- For waiting/grace periods: Provide precise duration from document
- For coverage questions: Start with "Yes" or "No", then explain briefly
- For amounts: Include exact figures with currency symbols
- Keep each answer 1-4 sentences maximum
- Use simple, clear language
- For Yes/No questions, start with clear Yes/No
- If not found: "Information not specified in document"

PROVIDE SIMPLE ACCURATE ANSWERS:"""

def optimized_gemini_call_v5(prompt):
    """V5: Optimized Gemini call balancing speed and accuracy"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Balanced settings for speed and accuracy
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low but not zero for better responses
                max_output_tokens=1000,  # Increased from 200 for better answers
                top_p=0.9,  # Higher for diverse responses
                top_k=30   # Balanced
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )
        
        if response and response.text:
            return response.text.strip()
        elif response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text.strip()
        
        return "Unable to generate response"
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return f"Error processing question"

def extract_answers_v5(doc_url, questions):
    """V5: Enhanced extraction combining V3 accuracy with speed optimization"""
    try:
        print("🚀 Starting V5 ENHANCED extraction...")
        start_time = time.time()
        
        # Step 1: V3-style PDF extraction with cleaning
        print("📄 Enhanced PDF extraction with cleaning...")
        pdf_text = download_and_extract_text_v5(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        extraction_time = time.time() - start_time
        print(f"📊 Extracted {len(pdf_text)} chars in {extraction_time:.2f}s")

        # Step 2: V3-style question preprocessing
        print("🔍 Preprocessing questions...")
        processed_questions = preprocess_questions_v5(questions)

        # Step 3: V3-style keyword extraction
        if len(pdf_text) > 25000:
            print("🧠 Large document - using enhanced keyword extraction...")
            processed_text = enhanced_keyword_search_v5(pdf_text, processed_questions)
        else:
            print("📋 Small document - using full content...")
            processed_text = pdf_text

        print(f"🔍 Processing {len(processed_text)} chars of relevant content")

        # Step 4: Format questions like V3
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(processed_questions)])
        
        # Step 5: Enhanced prompt
        prompt = enhanced_prompt_v5(questions_text, processed_text)
        
        # Step 6: Optimized API call
        print("🤖 Getting enhanced answers...")
        api_start = time.time()
        response = optimized_gemini_call_v5(prompt)
        api_time = time.time() - api_start
        print(f"🤖 API response in {api_time:.2f}s")
        
        # Step 7: V3-style parsing with validation
        answers = enhanced_parse_with_validation_v5(response, len(questions), questions)
        
        total_time = time.time() - start_time
        print(f"✅ V5 ENHANCED completed in {total_time:.2f}s total!")
        
        return answers
        
    except Exception as e:
        print(f"❌ Error in V5 extract_answers: {e}")
        return [f"V5 Error: {str(e)}"] * len(questions)

def enhanced_parse_with_validation_v5(text: str, expected_count: int, original_questions: List[str]) -> List[str]:
    """V5: Enhanced parsing based on V3 with validation"""
    answers = []
    
    # Strategy 1: V3-style numbered parsing
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches and len(matches) >= expected_count:
        for i in range(1, expected_count + 1):
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    # V3-style cleaning
                    clean_answer = answer_text.strip()
                    clean_answer = re.sub(r'\n+', ' ', clean_answer)
                    clean_answer = re.sub(r'\s+', ' ', clean_answer)
                    
                    # Remove formatting artifacts
                    clean_answer = re.sub(r'[📋"\'`]', '', clean_answer)
                    clean_answer = re.sub(r'Source:.*$', '', clean_answer, flags=re.MULTILINE)
                    
                    # V3-style validation
                    validated_answer = validate_answer_quality_v5(clean_answer, original_questions[i-1] if i <= len(original_questions) else "")
                    
                    answers.append(validated_answer)
                    break
    
    # Strategy 2: V3-style fallback parsing
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answers = []
        current_answer = ""
        
        for line in lines:
            if '📋' in line or 'Source:' in line:
                continue
                
            if re.match(r'^\d+\.', line):
                if current_answer:
                    validated = validate_answer_quality_v5(current_answer.strip(), "")
                    current_answers.append(validated)
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line
        
        if current_answer:
            validated = validate_answer_quality_v5(current_answer.strip(), "")
            current_answers.append(validated)
        
        # Fill gaps
        while len(answers) < expected_count and len(current_answers) > len(answers):
            answers.append(current_answers[len(answers)])
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Information not specified in document")
    
    return answers[:expected_count]

def validate_answer_quality_v5(answer: str, question: str) -> str:
    """V5: V3-style answer validation"""
    if not answer or len(answer.strip()) < 5:
        return "Information not specified in document"
    
    # Clean the answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # V3-style non-answer detection
    non_answers = [
        'not mentioned', 'not specified', 'not found', 'unclear', 
        'cannot determine', 'unable to find', 'no information'
    ]
    
    if any(pattern in answer.lower() for pattern in non_answers):
        return "Information not specified in document"
    
    # V3-style Yes/No question handling
    if question and ('does' in question.lower() or 'is' in question.lower()) and question.endswith('?'):
        if not (answer.lower().startswith('yes') or answer.lower().startswith('no')):
            if 'cover' in answer.lower() or 'include' in answer.lower() or 'available' in answer.lower():
                answer = "Yes, " + answer
            elif 'not' in answer.lower() or 'exclude' in answer.lower():
                answer = "No, " + answer
    
    # Limit to 4 sentences for simplicity
    sentences = re.split(r'[.!?]+', answer)
    if len(sentences) > 4:
        answer = '. '.join(sentences[:4]) + '.'
    
    return answer

# ✅ Test function for V5
if __name__ == "__main__":
    import time
    start_time = time.time()
    
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    
    # Test questions like V3
    questions = [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for PED to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the room rent limit for Plan A?",
        "Are AYUSH treatments covered under this policy?"
    ]
    
    print("🧪 Testing V5 ENHANCED Logic...")
    answers = extract_answers_v5(url, questions)
    
    end_time = time.time()
    print(f"\n⏱️ V5 Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")
        print("---" * 20)