import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List
import json

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text_v3(pdf_url):
    """Download PDF and extract ALL text with advanced cleaning - V3"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with open("temp_v3.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp_v3.pdf")
        text = ""
        
        # Process ALL pages with enhanced metadata
        for page_num in range(doc.page_count):
            page_text = doc[page_num].get_text()
            
            # Advanced text cleaning for better accuracy
            page_text = clean_extracted_text_v3(page_text)
            
            # Add enhanced page markers
            text += f"\n--- PAGE {page_num + 1} ---\n{page_text}\n"
            
        doc.close()
        
        # Clean up temp file
        if os.path.exists("temp_v3.pdf"):
            os.remove("temp_v3.pdf")
            
        return text
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists("temp_v3.pdf"):
            os.remove("temp_v3.pdf")
        raise e

def clean_extracted_text_v3(text):
    """Advanced text cleaning for better accuracy"""
    # Fix common OCR errors
    text = re.sub(r'\bO\b(?=\d)', '0', text)  # O to 0 in numbers
    text = re.sub(r'\bl\b(?=\d)', '1', text)  # l to 1 in numbers
    
    # Normalize currency symbols
    text = re.sub(r'\bRs\.?\s*', '₹', text)
    text = re.sub(r'\bINR\s*', '₹', text)
    
    # Fix spacing issues
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean paragraph breaks
    
    # Fix common formatting issues
    text = re.sub(r'(\d+)\s*%', r'\1%', text)  # Fix percentage spacing
    text = re.sub(r'(\d+)\s*₹', r'₹\1', text)  # Fix currency spacing
    
    return text.strip()

def enhanced_keyword_search_v3(text, questions):
    """Advanced keyword-based relevant section finder with domain expertise"""
    # Extract keywords from questions with better processing
    all_keywords = []
    for question in questions:
        # Extract meaningful words (3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
        
        # Extract abbreviations and important terms
        abbrevs = re.findall(r'\b[A-Z]{2,}\b', question)  # PED, ICU, etc.
        all_keywords.extend([abbrev.lower() for abbrev in abbrevs])
    
    # Enhanced stop words removal
    stop_words = {
        'what', 'when', 'where', 'does', 'this', 'policy', 'under', 'with', 
        'from', 'that', 'have', 'will', 'can', 'are', 'the', 'and', 'for',
        'how', 'why', 'who', 'which', 'any', 'all', 'some', 'may', 'must',
        'not', 'but', 'his', 'her', 'you', 'your', 'our', 'their'
    }
    
    # Domain-specific important terms (boost relevance)
    domain_terms = {
        'insurance': ['premium', 'coverage', 'deductible', 'claim', 'benefit', 'exclusion', 'rider'],
        'medical': ['treatment', 'hospital', 'surgery', 'diagnosis', 'therapy', 'doctor', 'patient'],
        'financial': ['amount', 'limit', 'payment', 'cost', 'fee', 'charge', 'expense'],
        'time': ['period', 'waiting', 'grace', 'duration', 'months', 'years', 'days'],
        'legal': ['terms', 'conditions', 'clause', 'section', 'provision']
    }
    
    keywords = list(set(word for word in all_keywords if word not in stop_words))
    
    # Split text into sections with better overlap handling
    sections = text.split('\n--- PAGE')
    relevant_sections = []
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        
        # Calculate relevance score
        relevance = 0
        
        # Basic keyword matches
        for keyword in keywords:
            if keyword in section_lower:
                relevance += 1
        
        # Bonus for domain-specific terms
        for category, terms in domain_terms.items():
            for term in terms:
                if term in section_lower:
                    relevance += 2  # Higher weight for domain terms
        
        # Bonus for sections with high keyword density
        if relevance > 3:
            relevance += 2
            
        # Bonus for sections with numerical data
        if re.search(r'\d+\s*(%|months?|years?|days?|₹)', section_lower):
            relevance += 1
            
        if relevance > 0:
            relevant_sections.append((section, relevance))
    
    # Sort by relevance and combine top sections with overlap
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    combined_text = ""
    for section, score in relevant_sections[:25]:  # Increased from 20 to 25
        combined_text += section + "\n"
        if len(combined_text) > 30000:  # Increased from 25000
            break
    
    return combined_text if combined_text else text[:30000]

def preprocess_questions_v3(questions):
    """Enhanced question preprocessing for better understanding"""
    processed_questions = []
    
    # Common abbreviation expansions
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
        # Expand abbreviations
        processed_question = question
        for abbrev, expansion in abbreviations.items():
            processed_question = re.sub(rf'\b{abbrev}\b', expansion, processed_question, flags=re.IGNORECASE)
        
        # Add context to common terms
        if 'grace period' in processed_question.lower() and 'premium' not in processed_question.lower():
            processed_question = processed_question.replace('grace period', 'grace period for premium payments')
        
        if 'waiting period' in processed_question.lower() and 'disease' not in processed_question.lower():
            processed_question = processed_question.replace('waiting period', 'waiting period for diseases or conditions')
        
        processed_questions.append(processed_question)
    
    return processed_questions

def ultra_enhanced_prompt_v3(questions_text, processed_text):
    """Ultra-enhanced prompt with all accuracy improvements"""
    return f"""EXPERT DOCUMENT ANALYZER - MAXIMUM ACCURACY MODE

You are an expert document analyst specializing in extracting precise, factual information. Analyze the document thoroughly and provide highly accurate answers.

DOCUMENT CONTENT:
{processed_text}

QUESTIONS TO ANALYZE:
{questions_text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract EXACT numerical values with proper units (30 days, 36 months, 2 years, 5%, ₹10,000)
- For waiting/grace periods: Provide precise duration from the document
- For coverage questions: Start with "Yes" or "No", then explain conditions clearly
- For amount/percentage questions: Include exact figures with currency symbols
- For definition questions: Use the document's exact terminology
- For conditional answers: List all conditions clearly
- If multiple time periods exist, specify which applies to what

ANSWER FORMAT RULES:
- Keep each answer 1-4 sentences maximum
- Use simple, clear language without jargon
- Include specific numbers, dates, percentages exactly as stated
- For Yes/No questions, start with clear Yes/No
- No citations, quotes, or special formatting
- If unclear or not found: "Information not clearly specified in document"

PROVIDE ULTRA-ACCURATE ANSWERS:"""

def advanced_gemini_call_v3(prompt):
    """Advanced Gemini API call with optimized settings for accuracy"""
    try:
        # Use reliable model with optimized settings
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Slight increase for better variety
                max_output_tokens=2000,  # Increased for detailed answers
                top_p=0.9,  # Increased for more diverse responses
                top_k=40   # Increased for better word choices
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )
        
        # Enhanced response extraction with fallbacks
        if response and response.text:
            return response.text.strip()
        elif response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text.strip()
        
        return "Unable to generate response from AI model"
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Fallback with simpler prompt
        try:
            simple_prompt = prompt.replace("ULTRA-ACCURATE", "SIMPLE").replace("CRITICAL ACCURACY", "BASIC")[:4000]
            simple_response = model.generate_content(simple_prompt)
            if simple_response and simple_response.text:
                return simple_response.text.strip()
        except:
            pass
        
        return f"AI model error: {str(e)}"

def extract_answers_v3(doc_url, questions):
    """V3 Ultra-Enhanced answer extraction with maximum accuracy"""
    try:
        print("🚀 Starting V3 ULTRA-ENHANCED extraction...")
        
        # Step 1: Download and extract with advanced cleaning
        print("📄 Downloading and extracting PDF with advanced cleaning...")
        pdf_text = download_and_extract_text_v3(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        print(f"📊 Extracted {len(pdf_text)} characters from PDF")

        # Step 2: Preprocess questions for better understanding
        print("🔍 Preprocessing questions for enhanced understanding...")
        processed_questions = preprocess_questions_v3(questions)

        # Step 3: Advanced keyword-based section extraction
        if len(pdf_text) > 30000:
            print("🧠 Large document - using ADVANCED keyword extraction...")
            processed_text = enhanced_keyword_search_v3(pdf_text, processed_questions)
        else:
            print("📋 Small document - using full content with cleaning...")
            processed_text = pdf_text

        print(f"🔍 Processing {len(processed_text)} characters of highly relevant content")

        # Step 4: Enhanced question formatting
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(processed_questions)])
        
        # Step 5: Create ultra-enhanced prompt
        prompt = ultra_enhanced_prompt_v3(questions_text, processed_text)
        
        # Step 6: Advanced API call with optimal settings
        print("🤖 Sending to Gemini with ULTRA-ENHANCED prompt...")
        response_text = advanced_gemini_call_v3(prompt)
        
        if "error" in response_text.lower() and "ai model error" in response_text.lower():
            return [response_text] * len(questions)

        # Step 7: Advanced response parsing with validation
        print("📝 Parsing with advanced validation...")
        answers = advanced_parse_with_validation_v3(response_text, len(questions), questions)
        
        print("✅ V3 ULTRA-ENHANCED extraction completed!")
        return answers
        
    except Exception as e:
        print(f"❌ Error in V3 extract_answers: {e}")
        return [f"V3 Error: {str(e)}"] * len(questions)

def advanced_parse_with_validation_v3(text: str, expected_count: int, original_questions: List[str]) -> List[str]:
    """Advanced parsing with answer validation"""
    answers = []
    
    # Strategy 1: Enhanced numbered parsing
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches and len(matches) >= expected_count:
        for i in range(1, expected_count + 1):
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    # Advanced cleaning
                    clean_answer = answer_text.strip()
                    clean_answer = re.sub(r'\n+', ' ', clean_answer)
                    clean_answer = re.sub(r'\s+', ' ', clean_answer)
                    
                    # Remove formatting artifacts
                    clean_answer = re.sub(r'[📋"\'`]', '', clean_answer)
                    clean_answer = re.sub(r'Source:.*$', '', clean_answer, flags=re.MULTILINE)
                    
                    # Validate answer quality
                    validated_answer = validate_answer_quality_v3(clean_answer, original_questions[i-1] if i <= len(original_questions) else "")
                    
                    answers.append(validated_answer)
                    break
    
    # Strategy 2: Enhanced fallback parsing
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answers = []
        current_answer = ""
        
        for line in lines:
            if '📋' in line or 'Source:' in line:
                continue
                
            if re.match(r'^\d+\.', line):
                if current_answer:
                    validated = validate_answer_quality_v3(current_answer.strip(), "")
                    current_answers.append(validated)
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line
        
        if current_answer:
            validated = validate_answer_quality_v3(current_answer.strip(), "")
            current_answers.append(validated)
        
        # Fill gaps with fallback answers
        while len(answers) < expected_count and len(current_answers) > len(answers):
            answers.append(current_answers[len(answers)])
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Information not clearly specified in document")
    
    return answers[:expected_count]

def validate_answer_quality_v3(answer: str, question: str) -> str:
    """Validate and improve answer quality"""
    if not answer or len(answer.strip()) < 5:
        return "Information not clearly specified in document"
    
    # Clean up the answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Check for common non-answer patterns
    non_answers = [
        'not mentioned', 'not specified', 'not found', 'unclear', 
        'cannot determine', 'unable to find', 'no information'
    ]
    
    if any(pattern in answer.lower() for pattern in non_answers):
        return "Information not clearly specified in document"
    
    # Ensure proper formatting for yes/no questions
    if question and ('does' in question.lower() or 'is' in question.lower()) and question.endswith('?'):
        if not (answer.lower().startswith('yes') or answer.lower().startswith('no')):
            # If it's clearly a yes/no question but answer doesn't start with yes/no
            if 'cover' in answer.lower() or 'include' in answer.lower() or 'available' in answer.lower():
                answer = "Yes, " + answer
            elif 'not' in answer.lower() or 'exclude' in answer.lower():
                answer = "No, " + answer
    
    return answer

# ✅ Test function for V3
if __name__ == "__main__":
    import time
    start_time = time.time()
    
    url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    questions = [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for PED to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the room rent limit for Plan A?",
        "Are AYUSH treatments covered under this policy?"
    ]
    
    print("🧪 Testing V3 ULTRA-ENHANCED Logic...")
    answers = extract_answers_v3(url, questions)
    
    end_time = time.time()
    print(f"\n⏱️ V3 Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")
        print("---" * 20)