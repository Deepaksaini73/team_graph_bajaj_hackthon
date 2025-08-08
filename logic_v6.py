import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
import time
from typing import List

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text_v6(pdf_url):
    """V6: Simple and robust PDF extraction (based on working V5 method)"""
    try:
        print(f"🔗 Downloading PDF...")
        
        # Simple, proven download method (like V5)
        response = requests.get(pdf_url, timeout=20)
        response.raise_for_status()
        
        print(f"✅ Downloaded {len(response.content)} bytes")
        
        with open("temp_v6.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp_v6.pdf")
        text = ""
        
        print(f"📚 Processing {doc.page_count} pages...")
        
        # Simple extraction like V5 (proven to work)
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            
            # Basic cleaning
            page_text = advanced_text_cleaning_v6(page_text)
            
            # Simple page markers
            text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            
        doc.close()
        
        if os.path.exists("temp_v6.pdf"):
            os.remove("temp_v6.pdf")
        
        print(f"✅ Extracted {len(text)} characters")
        return text
        
    except Exception as e:
        if os.path.exists("temp_v6.pdf"):
            os.remove("temp_v6.pdf")
        print(f"❌ PDF extraction error: {e}")
        raise e

def extract_text_from_dict_v6(text_dict):
    """V6: Fallback text extraction (not used in simple mode)"""
    text = ""
    if "blocks" in text_dict:
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            if "text" in span:
                                text += span["text"] + " "
                text += "\n"
    return text

def advanced_text_cleaning_v6(text):
    """V6: Enhanced text cleaning (based on V5 but improved)"""
    if not text:
        return ""
        
    # Fix common OCR errors (from V5)
    text = re.sub(r'\bO\b(?=\d)', '0', text)  # O to 0 in numbers
    text = re.sub(r'\bl\b(?=\d)', '1', text)  # l to 1 in numbers
    
    # Normalize currency symbols (from V5)
    text = re.sub(r'\bRs\.?\s*', '₹', text)
    text = re.sub(r'\bINR\s*', '₹', text)
    
    # Fix spacing issues (from V5)
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean paragraph breaks
    
    # Fix common formatting issues (from V5)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)  # Fix percentage spacing
    text = re.sub(r'(\d+)\s*₹', r'₹\1', text)  # Fix currency spacing
    
    return text.strip()

def intelligent_keyword_extraction_v6(text, questions):
    """V6: Smart keyword extraction (improved from V5)"""
    # Extract keywords like V5 but smarter
    all_keywords = []
    for question in questions:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
        
        # Extract abbreviations and important terms
        abbrevs = re.findall(r'\b[A-Z]{2,}\b', question)
        all_keywords.extend([abbrev.lower() for abbrev in abbrevs])
    
    # Enhanced stop words (from V5)
    stop_words = {
        'what', 'when', 'where', 'does', 'this', 'policy', 'under', 'with', 
        'from', 'that', 'have', 'will', 'can', 'are', 'the', 'and', 'for',
        'how', 'why', 'who', 'which', 'any', 'all', 'some', 'may', 'must',
        'not', 'but', 'his', 'her', 'you', 'your', 'our', 'their'
    }
    
    # V6: Enhanced domain-specific terms with higher weights
    domain_terms = {
        'insurance': ['premium', 'coverage', 'deductible', 'claim', 'benefit', 'exclusion', 'rider', 'sum', 'insured'],
        'medical': ['treatment', 'hospital', 'surgery', 'diagnosis', 'therapy', 'doctor', 'patient', 'maternity'],
        'financial': ['amount', 'limit', 'payment', 'cost', 'fee', 'charge', 'expense', 'room', 'rent'],
        'time': ['period', 'waiting', 'grace', 'duration', 'months', 'years', 'days'],
        'legal': ['terms', 'conditions', 'clause', 'section', 'provision', 'ayush']
    }
    
    keywords = list(set(word for word in all_keywords if word not in stop_words))
    
    # V6: Smarter section processing
    sections = text.split('\n--- PAGE')
    relevant_sections = []
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        relevance = 0
        
        # Basic keyword matches
        for keyword in keywords:
            if keyword in section_lower:
                relevance += 1
        
        # Domain-specific term matching with higher weight
        for category, terms in domain_terms.items():
            for term in terms:
                if term in section_lower:
                    relevance += 3  # Higher weight for domain terms
        
        # V6: Enhanced bonuses
        if relevance > 5:
            relevance += 3  # High relevance bonus
            
        # Numerical data bonus
        if re.search(r'\d+\s*(%|months?|years?|days?|₹)', section_lower):
            relevance += 2
            
        if relevance > 0:
            relevant_sections.append((section, relevance))
    
    # Sort and combine best sections
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    combined_text = ""
    for section, score in relevant_sections[:20]:  # Top 20 sections
        combined_text += section + "\n"
        if len(combined_text) > 25000:  # Reasonable limit
            break
    
    return combined_text if combined_text else text[:25000]

def smart_question_preprocessing_v6(questions):
    """V6: Enhanced question preprocessing (improved from V5)"""
    processed_questions = []
    
    # V6: More comprehensive abbreviation expansions
    abbreviations = {
        'PED': 'Pre-existing diseases',
        'ICU': 'Intensive Care Unit',
        'OPD': 'Outpatient Department',
        'IPD': 'Inpatient Department',
        'EMI': 'Equated Monthly Installment',
        'GST': 'Goods and Services Tax',
        'TPA': 'Third Party Administrator',
        'AYUSH': 'Ayurveda Yoga Unani Siddha Homeopathy',
        'NCD': 'No Claim Discount',
        'SI': 'Sum Insured'
    }
    
    for question in questions:
        # Expand abbreviations (like V5)
        processed_question = question
        for abbrev, expansion in abbreviations.items():
            processed_question = re.sub(rf'\b{abbrev}\b', expansion, processed_question, flags=re.IGNORECASE)
        
        # V6: Enhanced context enhancement
        if 'grace period' in processed_question.lower() and 'premium' not in processed_question.lower():
            processed_question = processed_question.replace('grace period', 'grace period for premium payments')
        
        if 'waiting period' in processed_question.lower() and 'disease' not in processed_question.lower():
            processed_question = processed_question.replace('waiting period', 'waiting period for diseases or conditions')
        
        if 'room rent' in processed_question.lower() and 'limit' not in processed_question.lower():
            processed_question = processed_question.replace('room rent', 'room rent limit')
        
        processed_questions.append(processed_question)
    
    return processed_questions

def master_prompt_v6(questions_text, processed_text):
    """V6: Master prompt engineering (improved from V5)"""
    return f"""EXPERT INSURANCE DOCUMENT ANALYZER - V6 PRECISION MODE

You are a world-class insurance document analyst with perfect accuracy. Analyze the document and provide precise answers.

DOCUMENT CONTENT:
{processed_text}

QUESTIONS TO ANALYZE:
{questions_text}

V6 ANSWER REQUIREMENTS:
✓ Extract EXACT numerical values with units (30 days, 36 months, 2 years, 5%, ₹10,000)
✓ For waiting/grace periods: Provide precise duration from document
✓ For coverage questions: Start with "Yes" or "No", then explain briefly in 2-3 sentences
✓ For amounts/limits: Include exact figures with currency symbols
✓ Keep each answer 1-4 sentences maximum - BE CONCISE
✓ Use simple, clear professional language
✓ For Yes/No questions, start with clear Yes/No
✓ If not found: "Information not specified in document"
✓ Number your answers clearly (1., 2., 3., etc.)

PROVIDE PRECISE ACCURATE ANSWERS:"""

def optimized_gemini_v6(prompt):
    """V6: Optimized Gemini call (improved from V5)"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # V6: Balanced settings for speed and accuracy
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low but not zero for better responses
                max_output_tokens=1000,  # Balanced for good answers
                top_p=0.9,  # High for comprehensive responses
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
        
        # V6: Enhanced fallback - FIXED SYNTAX ERROR
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            simple_prompt = f"Answer these questions from the document in 1-4 sentences each:\n{prompt[-2000:]}"
            simple_response = model.generate_content(
                simple_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=800)
            )
            if simple_response and simple_response.text:
                return simple_response.text.strip()
        except:
            pass
        
        return "Error processing questions"

def extract_answers_v6(doc_url, questions):
    """V6: Master extraction combining V5 reliability with V6 enhancements"""
    try:
        print("🚀 Starting V6 MASTER extraction...")
        start_time = time.time()
        
        # Step 1: Reliable PDF extraction (using V5 method)
        print("📄 Reliable PDF extraction...")
        pdf_text = download_and_extract_text_v6(doc_url)
        
        if not pdf_text.strip():
            print("❌ No text extracted")
            return ["No text found in document."] * len(questions)

        extraction_time = time.time() - start_time
        print(f"📊 Extracted {len(pdf_text)} chars in {extraction_time:.2f}s")

        # Step 2: Enhanced question preprocessing
        print("🧠 Enhanced question preprocessing...")
        processed_questions = smart_question_preprocessing_v6(questions)

        # Step 3: Smart keyword extraction
        if len(pdf_text) > 25000:
            print("🔍 Large document - using smart extraction...")
            processed_text = intelligent_keyword_extraction_v6(pdf_text, processed_questions)
        else:
            print("📋 Small document - using full content...")
            processed_text = pdf_text

        print(f"🔍 Processing {len(processed_text)} chars of relevant content")

        # Step 4: Create enhanced prompt
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(processed_questions)])
        prompt = master_prompt_v6(questions_text, processed_text)
        
        # Step 5: Optimized API call
        print("🤖 Getting V6 enhanced answers...")
        api_start = time.time()
        response = optimized_gemini_v6(prompt)
        api_time = time.time() - api_start
        print(f"🤖 API response in {api_time:.2f}s")
        
        # Step 6: Enhanced parsing
        answers = master_parse_v6(response, len(questions), questions)
        
        total_time = time.time() - start_time
        print(f"✅ V6 MASTER completed in {total_time:.2f}s total!")
        
        return answers
        
    except Exception as e:
        print(f"❌ Error in V6 extract_answers: {e}")
        return [f"V6 Error: {str(e)}"] * len(questions)

def master_parse_v6(text: str, expected_count: int, original_questions: List[str]) -> List[str]:
    """V6: Enhanced parsing (improved from V5)"""
    answers = []
    
    # Strategy 1: Numbered parsing (like V5 but enhanced)
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches and len(matches) >= expected_count:
        for i in range(1, expected_count + 1):
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    # V6: Enhanced cleaning
                    clean_answer = clean_and_validate_answer_v6(answer_text.strip(), original_questions[i-1] if i <= len(original_questions) else "")
                    answers.append(clean_answer)
                    break
    
    # Strategy 2: Fallback parsing (like V5)
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answers = []
        current_answer = ""
        
        for line in lines:
            if re.match(r'^\d+\.', line):
                if current_answer:
                    validated = clean_and_validate_answer_v6(current_answer.strip(), "")
                    current_answers.append(validated)
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line
        
        if current_answer:
            validated = clean_and_validate_answer_v6(current_answer.strip(), "")
            current_answers.append(validated)
        
        # Fill gaps
        while len(answers) < expected_count and len(current_answers) > len(answers):
            answers.append(current_answers[len(answers)])
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Information not specified in document")
    
    return answers[:expected_count]

def clean_and_validate_answer_v6(answer: str, question: str) -> str:
    """V6: Enhanced answer validation (improved from V5)"""
    if not answer or len(answer.strip()) < 3:
        return "Information not specified in document"
    
    # Clean the answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # V6: Enhanced non-answer detection
    non_answers = [
        'not mentioned', 'not specified', 'not found', 'unclear', 
        'cannot determine', 'unable to find', 'no information',
        'not available', 'not stated', 'not clear'
    ]
    
    if any(pattern in answer.lower() for pattern in non_answers):
        return "Information not specified in document"
    
    # V6: Enhanced Yes/No question handling
    if question and ('does' in question.lower() or 'is' in question.lower() or 'are' in question.lower()) and question.endswith('?'):
        if not (answer.lower().startswith('yes') or answer.lower().startswith('no')):
            if any(word in answer.lower() for word in ['cover', 'include', 'available', 'provided']):
                answer = "Yes, " + answer
            elif any(word in answer.lower() for word in ['not', 'exclude', 'does not', 'unavailable']):
                answer = "No, " + answer
    
    # Limit to 4 sentences for simplicity
    sentences = re.split(r'[.!?]+', answer)
    if len(sentences) > 4:
        answer = '. '.join(sentences[:4]) + '.'
    
    return answer

# ✅ Test function for V6
if __name__ == "__main__":
    start_time = time.time()
    
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    
    questions = [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for PED to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the room rent limit for Plan A?",
        "Are AYUSH treatments covered under this policy?"
    ]
    
    print("🧪 Testing V6 MASTER Logic...")
    answers = extract_answers_v6(url, questions)
    
    end_time = time.time()
    print(f"\n⏱️ V6 Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")
        print("---" * 20)