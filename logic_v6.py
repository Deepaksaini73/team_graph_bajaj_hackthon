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
    """V6: Lightning-fast PDF extraction with enhanced error handling"""
    try:
        response = requests.get(pdf_url, timeout=25, stream=True)
        response.raise_for_status()
        
        with open("temp_v6.pdf", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        doc = fitz.open("temp_v6.pdf")
        text = ""
        
        # Enhanced extraction with fallback methods
        for page_num in range(doc.page_count):
            try:
                # Primary method: Standard text extraction
                page_text = doc[page_num].get_text()
                
                # Fallback method: Dict extraction for better structure
                if len(page_text.strip()) < 50:
                    text_dict = doc[page_num].get_text("dict")
                    page_text = extract_text_from_dict_v6(text_dict)
                
                # Enhanced text cleaning
                page_text = advanced_text_cleaning_v6(page_text)
                
                # Smart page markers with content preview
                preview = page_text[:100].replace('\n', ' ')
                text += f"\n=== PAGE {page_num + 1} [{preview}...] ===\n{page_text}\n"
                
            except Exception as e:
                print(f"Warning: Error processing page {page_num + 1}: {e}")
                continue
            
        doc.close()
        
        if os.path.exists("temp_v6.pdf"):
            os.remove("temp_v6.pdf")
            
        return text
    except Exception as e:
        if os.path.exists("temp_v6.pdf"):
            os.remove("temp_v6.pdf")
        raise e

def extract_text_from_dict_v6(text_dict):
    """V6: Extract text from PyMuPDF dict structure"""
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
    """V6: Advanced text cleaning with pattern recognition"""
    # Fix OCR errors with context awareness
    text = re.sub(r'\bO(?=\d)', '0', text)  # O to 0 before digits
    text = re.sub(r'\bl(?=\d)', '1', text)  # l to 1 before digits
    text = re.sub(r'\bS(?=\d)', '5', text)  # S to 5 before digits
    text = re.sub(r'(?<=\d)O\b', '0', text)  # O to 0 after digits
    
    # Enhanced currency normalization
    text = re.sub(r'\b(?:Rs\.?|INR|Rupees?)\s*', '₹', text, flags=re.IGNORECASE)
    text = re.sub(r'₹\s*(\d)', r'₹\1', text)
    
    # Time period standardization
    text = re.sub(r'(\d+)\s*(?:months?|MONTHS?|Months?)', r'\1 months', text)
    text = re.sub(r'(\d+)\s*(?:years?|YEARS?|Years?)', r'\1 years', text)
    text = re.sub(r'(\d+)\s*(?:days?|DAYS?|Days?)', r'\1 days', text)
    
    # Percentage and number formatting
    text = re.sub(r'(\d+)\s*%', r'\1%', text)
    text = re.sub(r'(\d+)\s*(?:lakh|crore)', r'\1 \2', text, flags=re.IGNORECASE)
    
    # Fix broken words and sentences
    text = re.sub(r'([a-z])\s*\n\s*([a-z])', r'\1\2', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def intelligent_keyword_extraction_v6(text, questions):
    """V6: Intelligent keyword extraction with semantic grouping"""
    all_keywords = []
    important_phrases = []
    question_types = []
    
    for question in questions:
        # Classify question type for better processing
        q_lower = question.lower()
        if any(word in q_lower for word in ['what is', 'how much', 'amount', 'limit']):
            question_types.append('factual')
        elif any(word in q_lower for word in ['does', 'is', 'are', 'can']):
            question_types.append('boolean')
        elif any(word in q_lower for word in ['when', 'how long', 'period']):
            question_types.append('temporal')
        else:
            question_types.append('general')
        
        # Extract keywords with context
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        all_keywords.extend(words)
        
        # Extract important phrases
        phrases = re.findall(r'\b(?:grace period|waiting period|pre.?existing|maternity|room rent|sum insured|deductible|co.?payment)\b', question.lower())
        important_phrases.extend(phrases)
        
        # Extract abbreviations
        abbrevs = re.findall(r'\b[A-Z]{2,}\b', question)
        all_keywords.extend([abbrev.lower() for abbrev in abbrevs])
    
    # Enhanced stop words with domain awareness
    comprehensive_stop_words = {
        'what', 'when', 'where', 'does', 'this', 'policy', 'under', 'with', 'from', 'that',
        'have', 'will', 'can', 'are', 'the', 'and', 'for', 'how', 'why', 'who', 'which',
        'any', 'all', 'some', 'may', 'must', 'not', 'but', 'his', 'her', 'you', 'your',
        'our', 'their', 'has', 'had', 'been', 'being', 'have', 'do', 'did', 'should',
        'would', 'could', 'might', 'shall', 'will', 'can', 'may', 'must', 'ought'
    }
    
    # Domain-specific high-value terms with weights
    domain_categories = {
        'insurance_core': (['premium', 'coverage', 'deductible', 'claim', 'benefit', 'exclusion', 'rider', 'sum', 'insured'], 3),
        'medical_terms': (['treatment', 'hospital', 'surgery', 'diagnosis', 'therapy', 'doctor', 'patient', 'medical', 'clinical'], 3),
        'financial_data': (['amount', 'limit', 'payment', 'cost', 'fee', 'charge', 'expense', 'rate', 'percentage'], 2),
        'time_periods': (['period', 'waiting', 'grace', 'duration', 'months', 'years', 'days', 'continuous'], 2),
        'conditions': (['pre-existing', 'maternity', 'emergency', 'accident', 'illness', 'disease', 'chronic'], 2),
        'coverage_types': (['inpatient', 'outpatient', 'daycare', 'domiciliary', 'ambulance', 'preventive'], 2)
    }
    
    # Filter and weight keywords
    keywords = list(set(word for word in all_keywords if word not in comprehensive_stop_words))
    
    # Smart section extraction with relevance scoring
    sections = text.split('\n=== PAGE')
    relevant_sections = []
    
    for section_idx, section in enumerate(sections):
        section_lower = section.lower()
        relevance_score = 0
        
        # Basic keyword matching
        for keyword in keywords:
            if keyword in section_lower:
                relevance_score += 1
        
        # Important phrase matching (highest weight)
        for phrase in important_phrases:
            if phrase in section_lower:
                relevance_score += 5
        
        # Domain category matching with weights
        for category, (terms, weight) in domain_categories.items():
            for term in terms:
                if term in section_lower:
                    relevance_score += weight
        
        # Structure bonuses
        if re.search(r'(?:\d+\.|•|\*|\-)\s*[A-Z]', section):  # Lists/bullets
            relevance_score += 1
        
        if re.search(r'\b(?:table|schedule|annexure|appendix)\b', section_lower):  # Tables
            relevance_score += 2
            
        if re.search(r'\d+\s*(?:%|months?|years?|days?|₹|\$|lakh|crore)', section_lower):  # Numbers
            relevance_score += 2
            
        # Question type specific bonuses
        for q_type in question_types:
            if q_type == 'factual' and re.search(r'\d+', section):
                relevance_score += 1
            elif q_type == 'boolean' and any(word in section_lower for word in ['yes', 'no', 'covered', 'excluded']):
                relevance_score += 1
            elif q_type == 'temporal' and re.search(r'\d+\s*(?:months?|years?|days?)', section_lower):
                relevance_score += 2
        
        # High relevance bonus
        if relevance_score > 8:
            relevance_score += 3
            
        if relevance_score > 0:
            relevant_sections.append((section, relevance_score, section_idx))
    
    # Sort by relevance and select best sections
    relevant_sections.sort(key=lambda x: x[1], reverse=True)
    
    # Smart section combination with overlap prevention
    combined_text = ""
    used_sections = set()
    
    for section, score, idx in relevant_sections[:25]:
        if idx not in used_sections:
            combined_text += section + "\n"
            used_sections.add(idx)
            if len(combined_text) > 28000:  # Optimized limit
                break
    
    return combined_text if combined_text else text[:28000]

def smart_question_preprocessing_v6(questions):
    """V6: Smart question preprocessing with context enhancement"""
    processed_questions = []
    
    # Comprehensive abbreviation dictionary
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
        'SI': 'Sum Insured',
        'OPD': 'Out Patient Department',
        'CCU': 'Cardiac Care Unit',
        'ICCU': 'Intensive Cardiac Care Unit'
    }
    
    # Context enhancement patterns
    context_enhancements = {
        r'\bgrace period\b(?! for)': 'grace period for premium payment',
        r'\bwaiting period\b(?! for)': 'waiting period for coverage',
        r'\broom rent\b(?! limit|restriction)': 'room rent limit and restrictions',
        r'\bmaternity\b(?! expenses|coverage)': 'maternity expenses and coverage',
        r'\bdeductible\b(?! amount)': 'deductible amount and conditions'
    }
    
    for question in questions:
        processed_question = question
        
        # Expand abbreviations
        for abbrev, expansion in abbreviations.items():
            processed_question = re.sub(rf'\b{abbrev}\b', expansion, processed_question, flags=re.IGNORECASE)
        
        # Add context
        for pattern, replacement in context_enhancements.items():
            processed_question = re.sub(pattern, replacement, processed_question, flags=re.IGNORECASE)
        
        # Enhance question structure
        if processed_question.strip() and not processed_question.endswith('?'):
            processed_question += '?'
        
        processed_questions.append(processed_question)
    
    return processed_questions

def master_prompt_v6(questions_text, processed_text):
    """V6: Master prompt with advanced instructions"""
    return f"""EXPERT INSURANCE DOCUMENT ANALYZER - PRECISION MODE

You are a world-class insurance document analyst with perfect accuracy. Analyze the document and provide exactly what is asked.

DOCUMENT CONTENT:
{processed_text}

QUESTIONS TO ANSWER:
{questions_text}

CRITICAL INSTRUCTIONS:
✓ Extract EXACT numerical values with complete units (30 days, 24 months, 2 years, 5%, ₹50,000)
✓ For YES/NO questions: Start with "Yes" or "No", then explain in 1-3 sentences
✓ For amounts/limits: State exact figures with currency symbols as written
✓ For time periods: Specify exact duration and what it applies to
✓ For coverage questions: Clearly state what is covered and any conditions
✓ Use simple, professional language - maximum 4 sentences per answer
✓ If information is genuinely missing: "Information not specified in document"

ANSWER FORMAT:
- Direct, clear answers in 1-4 sentences
- Include specific numbers, percentages, amounts exactly as stated
- No extra formatting, quotes, or citations
- Professional but simple language

PROVIDE ACCURATE ANSWERS:"""

def optimized_gemini_v6(prompt):
    """V6: Optimized Gemini call with error recovery"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Optimized settings for accuracy and speed
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.05,  # Very low for consistency
                max_output_tokens=1200,  # Balanced for quality answers
                top_p=0.92,  # High for comprehensive responses
                top_k=35   # Balanced for word variety
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
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
        
        # Triple fallback strategy
        try:
            # Fallback 1: Simplified prompt
            simple_prompt = prompt.replace("PRECISION MODE", "SIMPLE MODE")[:5000]
            simple_response = model.generate_content(
                simple_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=800)
            )
            if simple_response and simple_response.text:
                return simple_response.text.strip()
        except:
            try:
                # Fallback 2: Basic prompt
                basic_prompt = f"Answer these questions from the document:\n{prompt[-2000:]}"
                basic_response = model.generate_content(basic_prompt)
                if basic_response and basic_response.text:
                    return basic_response.text.strip()
            except:
                pass
        
        return f"Error: Unable to process request"

def extract_answers_v6(doc_url, questions):
    """V6: Master extraction with all optimizations"""
    try:
        print("🚀 Starting V6 MASTER extraction...")
        start_time = time.time()
        
        # Step 1: Enhanced PDF extraction
        print("📄 Advanced PDF extraction with fallbacks...")
        pdf_text = download_and_extract_text_v6(doc_url)
        
        if not pdf_text.strip():
            return ["No text found in document."] * len(questions)

        extraction_time = time.time() - start_time
        print(f"📊 Extracted {len(pdf_text)} chars in {extraction_time:.2f}s")

        # Step 2: Smart question preprocessing
        print("🧠 Smart question preprocessing...")
        processed_questions = smart_question_preprocessing_v6(questions)

        # Step 3: Intelligent keyword extraction
        process_start = time.time()
        if len(pdf_text) > 28000:
            print("🔍 Large document - using intelligent extraction...")
            processed_text = intelligent_keyword_extraction_v6(pdf_text, processed_questions)
        else:
            print("📋 Document size optimal - using enhanced full content...")
            processed_text = pdf_text

        process_time = time.time() - process_start
        print(f"🔍 Processed {len(processed_text)} chars in {process_time:.2f}s")

        # Step 4: Create master prompt
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(processed_questions)])
        prompt = master_prompt_v6(questions_text, processed_text)
        
        # Step 5: Optimized API call
        print("🤖 Getting master-level answers...")
        api_start = time.time()
        response = optimized_gemini_v6(prompt)
        api_time = time.time() - api_start
        print(f"🤖 API response in {api_time:.2f}s")
        
        # Step 6: Master parsing
        print("📝 Master parsing with validation...")
        parse_start = time.time()
        answers = master_parse_v6(response, len(questions), questions)
        parse_time = time.time() - parse_start
        
        total_time = time.time() - start_time
        print(f"✅ V6 MASTER completed in {total_time:.2f}s!")
        print(f"   📊 Breakdown: Extract({extraction_time:.1f}s) + Process({process_time:.1f}s) + API({api_time:.1f}s) + Parse({parse_time:.1f}s)")
        
        return answers
        
    except Exception as e:
        print(f"❌ Error in V6 extract_answers: {e}")
        return [f"V6 Error: {str(e)}"] * len(questions)

def master_parse_v6(text: str, expected_count: int, original_questions: List[str]) -> List[str]:
    """V6: Master parsing with comprehensive validation"""
    answers = []
    
    # Strategy 1: Advanced numbered parsing
    pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    
    if matches and len(matches) >= expected_count:
        for i in range(1, expected_count + 1):
            found = False
            for num_str, answer_text in matches:
                if int(num_str) == i:
                    # Advanced cleaning and validation
                    clean_answer = clean_and_validate_answer_v6(
                        answer_text.strip(), 
                        original_questions[i-1] if i <= len(original_questions) else ""
                    )
                    answers.append(clean_answer)
                    found = True
                    break
            
            if not found:
                answers.append("Information not specified in document")
    
    # Strategy 2: Enhanced fallback parsing
    if len(answers) < expected_count:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        fallback_answers = []
        current_answer = ""
        
        for line in lines:
            if any(marker in line for marker in ['📋', 'Source:', '---']):
                continue
                
            if re.match(r'^\d+\.', line):
                if current_answer:
                    clean_ans = clean_and_validate_answer_v6(current_answer.strip(), "")
                    fallback_answers.append(clean_ans)
                current_answer = re.sub(r'^\d+\.\s*', '', line)
            else:
                current_answer += " " + line
        
        if current_answer:
            clean_ans = clean_and_validate_answer_v6(current_answer.strip(), "")
            fallback_answers.append(clean_ans)
        
        # Use fallback answers to fill gaps
        while len(answers) < expected_count and len(fallback_answers) > 0:
            if len(fallback_answers) > len(answers):
                answers.append(fallback_answers[len(answers)])
            else:
                break
    
    # Ensure exact count
    while len(answers) < expected_count:
        answers.append("Information not specified in document")
    
    return answers[:expected_count]

def clean_and_validate_answer_v6(answer: str, question: str) -> str:
    """V6: Advanced answer cleaning and validation"""
    if not answer or len(answer.strip()) < 3:
        return "Information not specified in document"
    
    # Clean the answer
    answer = re.sub(r'\n+', ' ', answer)
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Remove formatting artifacts
    answer = re.sub(r'[📋"\'`\*]', '', answer)
    answer = re.sub(r'Source:.*$', '', answer, flags=re.MULTILINE)
    
    # Check for non-answer patterns
    non_answers = [
        'not mentioned', 'not specified', 'not found', 'unclear', 'cannot determine',
        'unable to find', 'no information', 'not available', 'not stated', 'not clear'
    ]
    
    if any(pattern in answer.lower() for pattern in non_answers):
        return "Information not specified in document"
    
    # Enhanced Yes/No question handling
    if question:
        q_lower = question.lower()
        if ('does' in q_lower or 'is' in q_lower or 'are' in q_lower) and question.endswith('?'):
            answer_lower = answer.lower()
            if not (answer_lower.startswith('yes') or answer_lower.startswith('no')):
                # Smart yes/no detection
                positive_keywords = ['cover', 'include', 'available', 'provided', 'applicable', 'eligible', 'allowed']
                negative_keywords = ['not', 'exclude', 'does not', 'is not', 'are not', 'unavailable', 'excluded']
                
                if any(keyword in answer_lower for keyword in positive_keywords):
                    answer = "Yes, " + answer
                elif any(keyword in answer_lower for keyword in negative_keywords):
                    answer = "No, " + answer
    
    # Ensure proper sentence structure
    if not answer.endswith('.') and len(answer) > 10:
        answer += "."
    
    # Limit to 4 sentences maximum
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