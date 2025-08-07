import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import os
import re
from typing import List
import json
import time

# 👉 Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyC7wqktrMwFSs5SoqvyepwAImuga1zVCYw")

def download_and_extract_text_v4(pdf_url):
    """V4: Enhanced PDF extraction with better text preservation"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        with open("temp_v4.pdf", "wb") as f:
            f.write(response.content)

        doc = fitz.open("temp_v4.pdf")
        text = ""
        
        # Enhanced text extraction with multiple methods
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Method 1: Standard text extraction
            page_text = page.get_text()
            
            # Method 2: Text blocks extraction for better structure
            blocks = page.get_text("blocks")
            structured_text = ""
            for block in blocks:
                if len(block) >= 5 and block[4].strip():  # block[4] contains text
                    structured_text += block[4] + "\n"
            
            # Use structured text if it's more complete
            if len(structured_text) > len(page_text):
                page_text = structured_text
            
            # Advanced cleaning
            page_text = advanced_text_cleaning_v4(page_text)
            
            # Enhanced page markers with metadata
            text += f"\n=== PAGE {page_num + 1} ===\n{page_text}\n"
            
        doc.close()
        
        # Clean up temp file
        if os.path.exists("temp_v4.pdf"):
            os.remove("temp_v4.pdf")
            
        return text
    except Exception as e:
        if os.path.exists("temp_v4.pdf"):
            os.remove("temp_v4.pdf")
        raise e

def advanced_text_cleaning_v4(text):
    """V4: Advanced text cleaning with pattern recognition"""
    # Fix common OCR errors
    text = re.sub(r'\bO\b(?=\d)', '0', text)  # O to 0 in numbers
    text = re.sub(r'\bl\b(?=\d)', '1', text)  # l to 1 in numbers
    text = re.sub(r'\bS\b(?=\d)', '5', text)  # S to 5 in numbers
    
    # Normalize currency and percentages
    text = re.sub(r'\b(?:Rs\.?|INR)\s*', '₹', text)
    text = re.sub(r'(\d+)\s*%', r'\1%', text)
    text = re.sub(r'₹\s*(\d+)', r'₹\1', text)
    
    # Fix time periods
    text = re.sub(r'(\d+)\s*(?:months?|MONTHS?)', r'\1 months', text)
    text = re.sub(r'(\d+)\s*(?:years?|YEARS?)', r'\1 years', text)
    text = re.sub(r'(\d+)\s*(?:days?|DAYS?)', r'\1 days', text)
    
    # Clean spacing
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Fix broken sentences
    text = re.sub(r'([a-z])\s*\n\s*([a-z])', r'\1 \2', text)
    
    return text.strip()

def ultra_keyword_extraction_v4(text, questions):
    """V4: Ultra-advanced keyword extraction with semantic analysis"""
    # Extract all types of keywords
    all_keywords = []
    important_phrases = []
    
    for question in questions:
        # Extract words (3+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
        
        # Extract important phrases
        phrases = re.findall(r'\b(?:grace period|waiting period|pre.?existing|maternity|coverage|benefit|premium|deductible)\b', question.lower())
        important_phrases.extend(phrases)
        
        # Extract abbreviations
        abbrevs = re.findall(r'\b[A-Z]{2,}\b', question)
        all_keywords.extend([abbrev.lower() for abbrev in abbrevs])
        
        # Extract numerical context
        numerical_context = re.findall(r'\b(?:how much|what is|amount|percentage|rate|limit|maximum|minimum)\b', question.lower())
        all_keywords.extend(numerical_context)
    
    # Enhanced stop words
    stop_words = {
        'what', 'when', 'where', 'does', 'this', 'under', 'with', 'from', 'that', 'have', 
        'will', 'can', 'are', 'the', 'and', 'for', 'how', 'why', 'who', 'which', 'any', 
        'all', 'some', 'may', 'must', 'not', 'but', 'his', 'her', 'you', 'your', 'our', 'their'
    }
    
    # Domain-specific high-value terms
    high_value_terms = {
        'insurance': ['premium', 'coverage', 'deductible', 'claim', 'benefit', 'exclusion', 'rider', 'sum', 'insured'],
        'medical': ['treatment', 'hospital', 'surgery', 'diagnosis', 'therapy', 'doctor', 'patient', 'medical'],
        'financial': ['amount', 'limit', 'payment', 'cost', 'fee', 'charge', 'expense', 'rate', 'percentage'],
        'time': ['period', 'waiting', 'grace', 'duration', 'months', 'years', 'days', 'continuous'],
        'conditions': ['pre-existing', 'maternity', 'emergency', 'accident', 'illness', 'disease']
    }
    
    keywords = list(set(word for word in all_keywords if word not in stop_words))
    
    # Split text into enhanced sections
    sections = text.split('\n=== PAGE')
    relevant_sections = []
    
    for i, section in enumerate(sections):
        section_lower = section.lower()
        relevance = 0
        
        # Basic keyword matching
        for keyword in keywords:
            if keyword in section_lower:
                relevance += 1
        
        # Important phrase matching (higher weight)
        for phrase in important_phrases:
            if phrase in section_lower:
                relevance += 3
        
        # High-value term matching
        for category, terms in high_value_terms.items():
            for term in terms:
                if term in section_lower:
                    relevance += 2
        
        # Numerical data bonus
        if re.search(r'\d+\s*(?:%|months?|years?|days?|₹|\$)', section_lower):
            relevance += 2
        
        # Table/list structure bonus
        if re.search(r'(?:\d+\.|•|\*|\-)\s*[A-Z]', section):
            relevance += 1
        
        # High keyword density bonus
        if relevance > 5:
            relevance += 3
            
        if relevance > 0:
            relevant_sections.append((section, relevance))
    
    # Sort and combine with smart overlap
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    combined_text = ""
    for section, score in relevant_sections[:30]:  # Increased to 30 sections
        combined_text += section + "\n"
        if len(combined_text) > 35000:  # Increased context window
            break
    
    return combined_text if combined_text else text[:35000]

def intelligent_question_preprocessing_v4(questions):
    """V4: Intelligent question preprocessing with context enhancement"""
    processed_questions = []
    
    # Enhanced abbreviation dictionary
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
    
    # Context enhancement patterns
    context_patterns = {
        r'\bgrace period\b(?! for)': 'grace period for premium payment',
        r'\bwaiting period\b(?! for)': 'waiting period for coverage',
        r'\broom rent\b(?! limit)': 'room rent limit or restriction',
        r'\bcoverage\b(?! limit)': 'coverage benefits and limits',
        r'\bmaternity\b(?! expenses)': 'maternity expenses and benefits'
    }
    
    for question in questions:
        processed_question = question
        
        # Expand abbreviations
        for abbrev, expansion in abbreviations.items():
            processed_question = re.sub(rf'\b{abbrev}\b', expansion, processed_question, flags=re.IGNORECASE)
        
        # Add context
        for pattern, replacement in context_patterns.items():
            processed_question = re.sub(pattern, replacement, processed_question, flags=re.IGNORECASE)
        
        # Enhance question clarity
        if processed_question.endswith('?') and not processed_question.lower().startswith(('what', 'how', 'when', 'where', 'why', 'which', 'does', 'is', 'are')):
            processed_question = f"What information is available about: {processed_question[:-1]}?"
        
        processed_questions.append(processed_question)
    
    return processed_questions

def master_prompt_v4(questions_text, processed_text):
    """V4: Master-level prompt engineering for maximum accuracy"""
    return f"""EXPERT DOCUMENT ANALYSIS SYSTEM - ULTRA PRECISION MODE

You are a world-class document analyst with expertise in extracting precise, factual information. Your task is to provide the most accurate answers possible from the given document.

DOCUMENT CONTENT TO ANALYZE:
{processed_text}

QUESTIONS REQUIRING EXPERT ANALYSIS:
{questions_text}

ULTRA-PRECISION REQUIREMENTS:
- Extract EXACT numerical values with complete units (30 days, 36 months, 2 years, 5%, ₹10,000, etc.)
- For time periods: State precise duration exactly as written in document
- For Yes/No questions: Begin with clear "Yes" or "No", then provide complete explanation
- For monetary amounts: Include exact figures with proper currency symbols
- For percentages: Provide exact percentage values as stated
- For coverage questions: Detail specific conditions, limitations, and exclusions
- For waiting periods: Specify exact timeframes and what they apply to
- If multiple options exist: List all options clearly

CRITICAL ANSWER FORMAT:
- Each answer must be 1-4 sentences maximum
- Use simple, professional language
- Include ALL relevant numbers, dates, percentages exactly as stated
- For conditional answers: State all conditions clearly
- No formatting symbols, quotes, or citations
- If information is genuinely not in document: "Information not specified in document"

PROVIDE EXPERT-LEVEL ACCURATE ANSWERS:"""

def optimized_gemini_call_v4(prompt):
    """V4: Optimized Gemini API call with best settings"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Optimized generation settings based on testing
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.05,  # Very low for maximum consistency
                max_output_tokens=2500,  # Increased for detailed answers
                top_p=0.95,  # High for comprehensive responses
                top_k=50   # Increased for better word variety
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        # Enhanced response extraction
        if response and response.text:
            return response.text.strip()
        elif response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                return candidate.content.parts[0].text.strip()
        
        return "Unable to generate response from AI model"
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        
        # Multi-level fallback strategy
        try:
            # Fallback 1: Simpler prompt
            simple_prompt = prompt.replace("ULTRA-PRECISION", "BASIC").replace("EXPERT-LEVEL", "SIMPLE")[:6000]
            simple_response = model.generate_content(
                simple_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=1500)
            )
            if simple_response and simple_response.text:
                return simple_response.text.strip()
        except:
            pass
        
        return f"AI model error: {str(e)}"

def extract_answers_v4(doc_url, questions):
    """V4: Master-level answer extraction with maximum accuracy optimization"""
    try:
        print("🚀 Starting V4 MASTER-LEVEL extraction...")
        start_time = time.time()
        
        # Step 1: Enhanced PDF extraction
        print("📄 Downloading and extracting PDF with advanced methods...")
        pdf_text = download_and_extract_text_v4(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        extraction_time = time.time() - start_time
        print(f"📊 Extracted {len(pdf_text)} characters in {extraction_time:.2f}s")

        # Step 2: Intelligent question preprocessing
        print("🧠 Intelligent question preprocessing...")
        processed_questions = intelligent_question_preprocessing_v4(questions)

        # Step 3: Ultra-advanced keyword extraction
        process_start = time.time()
        if len(pdf_text) > 35000:
            print("🔍 Large document - using ULTRA-ADVANCED keyword extraction...")
            processed_text = ultra_keyword_extraction_v4(pdf_text, processed_questions)
        else:
            print("📋 Document size optimal - using full content with advanced cleaning...")
            processed_text = pdf_text

        process_time = time.time() - process_start
        print(f"🔍 Processed {len(processed_text)} chars in {process_time:.2f}s")

        # Step 4: Master-level question formatting
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(processed_questions)])
        
        # Step 5: Master prompt creation
        prompt = master_prompt_v4(questions_text, processed_text)
        
        # Step 6: Optimized API call
        print("🤖 Sending to Gemini with MASTER-LEVEL prompt...")
        api_start = time.time()
        response_text = optimized_gemini_call_v4(prompt)
        api_time = time.time() - api_start
        print(f"🤖 API response received in {api_time:.2f}s")
        
        if "error" in response_text.lower() and "ai model error" in response_text.lower():
            return [response_text] * len(questions)

        # Step 7: Master-level parsing
        print("📝 Master-level parsing with validation...")
        parse_start = time.time()
        answers = master_parse_with_validation_v4(response_text, len(questions), questions)
        parse_time = time.time() - parse_start
        
        total_time = time.time() - start_time
        print(f"✅ V4 MASTER extraction completed in {total_time:.2f}s total!")
        print(f"   📊 Breakdown: Extract({extraction_time:.1f}s) + Process({process_time:.1f}s) + API({api_time:.1f}s) + Parse({parse_time:.1f}s)")
        
        return answers
        
    except Exception as e:
        print(f"❌ Error in V4 extract_answers: {e}")
        return [f"V4 Error: {str(e)}"] * len(questions)

def master_parse_with_validation_v4(text: str, expected_count: int, original_questions: List[str]) -> List[str]:
    """V4: Master-level parsing with comprehensive validation"""
    answers = []
    
    # Strategy 1: Enhanced numbered parsing with validation
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches and len(matches) >= expected_count:
        for i in range(1, expected_count + 1):
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    # Master-level cleaning
                    clean_answer = answer_text.strip()
                    clean_answer = re.sub(r'\n+', ' ', clean_answer)
                    clean_answer = re.sub(r'\s+', ' ', clean_answer)
                    
                    # Remove artifacts
                    clean_answer = re.sub(r'[📋"\'`]', '', clean_answer)
                    clean_answer = re.sub(r'Source:.*$', '', clean_answer, flags=re.MULTILINE)
                    
                    # Master validation
                    validated_answer = master_answer_validation_v4(
                        clean_answer, 
                        original_questions[i-1] if i <= len(original_questions) else ""
                    )
                    
                    answers.append(validated_answer)
                    break
    
    # Strategy 2: Advanced fallback parsing
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        current_answers = []
        current_answer = ""
        
        for line in lines:
            if '📋' in line or 'Source:' in line:
                continue
                
            if re.match(r'^\d+\.', line):
                if current_answer:
                    validated = master_answer_validation_v4(current_answer.strip(), "")
                    current_answers.append(validated)
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line
        
        if current_answer:
            validated = master_answer_validation_v4(current_answer.strip(), "")
            current_answers.append(validated)
        
        # Fill gaps
        while len(answers) < expected_count and len(current_answers) > len(answers):
            answers.append(current_answers[len(answers)])
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Information not specified in document")
    
    return answers[:expected_count]

def master_answer_validation_v4(answer: str, question: str) -> str:
    """V4: Master-level answer validation and enhancement"""
    if not answer or len(answer.strip()) < 3:
        return "Information not specified in document"
    
    # Clean the answer
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Check for non-answer patterns
    non_answers = [
        'not mentioned', 'not specified', 'not found', 'unclear', 'cannot determine', 
        'unable to find', 'no information', 'not available', 'not stated'
    ]
    
    if any(pattern in answer.lower() for pattern in non_answers):
        return "Information not specified in document"
    
    # Enhanced Yes/No question handling
    if question:
        question_lower = question.lower()
        if ('does' in question_lower or 'is' in question_lower or 'are' in question_lower) and question.endswith('?'):
            if not (answer.lower().startswith('yes') or answer.lower().startswith('no')):
                # Intelligent yes/no detection
                positive_indicators = ['cover', 'include', 'available', 'provided', 'applicable', 'eligible']
                negative_indicators = ['not', 'exclude', 'does not', 'is not', 'are not', 'unavailable']
                
                answer_lower = answer.lower()
                if any(indicator in answer_lower for indicator in positive_indicators):
                    answer = "Yes, " + answer
                elif any(indicator in answer_lower for indicator in negative_indicators):
                    answer = "No, " + answer
    
    # Ensure proper formatting
    if not answer.endswith('.') and len(answer) > 10:
        answer += "."
    
    return answer

# ✅ Test function for V4
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
    
    print("🧪 Testing V4 MASTER-LEVEL Logic...")
    answers = extract_answers_v4(url, questions)
    
    end_time = time.time()
    print(f"\n⏱️ V4 Total time: {end_time - start_time:.2f} seconds")
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\n{i}. Q: {q}")
        print(f"   A: {a}")
        print("---" * 20)