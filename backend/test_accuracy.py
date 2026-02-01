"""
Chatbot accuracy testing script.

Tests the chatbot with predefined questions and evaluates:
1. Does it retrieve the correct sources?
2. Does it provide accurate answers?
3. Does it avoid common mistakes (lisans vs lisansüstü, etc.)?

Usage:
    python test_accuracy.py
"""
import json
import sys
from pathlib import Path
from typing import Dict, List
from colorama import init, Fore, Style

sys.path.insert(0, str(Path(__file__).parent))

from app.llm import ResponseGenerator

# Initialize colorama for colored output
init(autoreset=True)


def load_test_questions(filepath: str = "test_questions.json") -> List[Dict]:
    """Load test questions from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_questions']


def evaluate_response(question: Dict, response: Dict) -> Dict:
    """
    Evaluate chatbot response against expected answer.
    
    Returns:
        dict with evaluation results
    """
    result = {
        "question_id": question['id'],
        "category": question['category'],
        "question": question['question'],
        "expected_answer": question['expected_answer'],
        "expected_source": question['expected_source'],
        "actual_answer": response.get('answer', ''),
        "actual_sources": [s.get('title', '') for s in response.get('sources', [])],  # Fixed: 'source' → 'title'
        "source_match": False,
        "answer_quality": "NOT_EVALUATED",
        "notes": []
    }
    
    # Check if expected source is present
    expected_src = question['expected_source']
    actual_sources_str = ' '.join(result['actual_sources']).lower()
    
    if expected_src == "META_RESPONSE":
        # Meta question - check if it's a self-description
        if "subu" in response['answer'].lower() and "mevzuat" in response['answer'].lower():
            result['source_match'] = True
            result['answer_quality'] = "GOOD"
        else:
            result['notes'].append("Meta response should introduce the chatbot")
    
    elif expected_src == "NONE_OR_CLARIFICATION":
        # Should clarify or say "no info"
        if any(word in response['answer'].lower() for word in ['üzgünüm', 'bulamadım', 'lisansüstü', 'tez']):
            result['source_match'] = True
            result['answer_quality'] = "GOOD"
        else:
            result['notes'].append("Should clarify that this is for graduate students")
    
    elif expected_src == "NOT_YURT_DISI_KABULU":
        # Should NOT mention yurt dışı
        if "yurt dışı" in response['answer'].lower() or "yurt dışından" in response['answer'].lower():
            result['source_match'] = False
            result['answer_quality'] = "BAD"
            result['notes'].append("❌ WRONG: Mentions 'yurt dışı' for domestic students!")
        else:
            result['source_match'] = True
            result['answer_quality'] = "GOOD"
    
    elif expected_src == "MULTIPLE_WITH_WARNING":
        # Should provide general info and optionally mention that specific details are not in regulations
        # GOOD: Has general info + warning note
        # PARTIAL: Has general info but no warning note
        # POOR: Wrong info or no info
        answer_lower = response['answer'].lower()
        
        # Check if it provides general information (not checking for specific warning)
        if any(word in answer_lower for word in ['mezuniyet', 'not', 'başarı', 'lisans']):
            result['source_match'] = True
            
            # Check if it includes a warning about missing specific details
            if ("mevzuat" in answer_lower and ("belirtilmemiş" in answer_lower or "belirtilmemektedir" in answer_lower)) or \
               "öğrenci işleri" in answer_lower:
                result['answer_quality'] = "GOOD"
            else:
                result['answer_quality'] = "PARTIAL"
                result['notes'].append("⚠️ Could mention that specific details (GANO, credits) are not explicitly stated in regulations")
        else:
            result['answer_quality'] = "POOR"
            result['notes'].append("Should provide relevant general information")
    
    else:
        # Check if expected source is in actual sources
        expected_src_lower = expected_src.lower()
        for src in result['actual_sources']:
            if expected_src_lower in src.lower():
                result['source_match'] = True
                break
        
        if not result['source_match']:
            result['notes'].append(f"Expected source '{expected_src}' not found")
    
    # Check if expected answer keywords are in actual answer
    if result['answer_quality'] == "NOT_EVALUATED":
        expected_keywords = question['expected_answer'].lower().split()
        actual_answer_lower = response['answer'].lower()
        
        # Simple keyword match (can be improved with semantic similarity)
        matches = sum(1 for kw in expected_keywords if kw in actual_answer_lower)
        match_ratio = matches / len(expected_keywords) if expected_keywords else 0
        
        if match_ratio >= 0.6:
            result['answer_quality'] = "GOOD"
        elif match_ratio >= 0.3:
            result['answer_quality'] = "PARTIAL"
        else:
            result['answer_quality'] = "POOR"
            result['notes'].append(f"Expected keywords not found: {question['expected_answer']}")
    
    return result


def print_result(result: Dict):
    """Print evaluation result with colors."""
    qid = result['question_id']
    category = result['category']
    question = result['question']
    
    # Header
    print(f"\n{'='*80}")
    print(f"{Fore.CYAN}[Test {qid}] {category}")
    print(f"{Fore.WHITE}Q: {question}")
    
    # Source match
    if result['source_match']:
        print(f"{Fore.GREEN}✓ Source: CORRECT")
    else:
        print(f"{Fore.RED}✗ Source: INCORRECT")
        print(f"  Expected: {result['expected_source']}")
        print(f"  Got: {', '.join(result['actual_sources'][:3])}")
    
    # Answer quality
    quality = result['answer_quality']
    if quality == "GOOD":
        print(f"{Fore.GREEN}✓ Answer: GOOD")
    elif quality == "PARTIAL":
        print(f"{Fore.YELLOW}⚠ Answer: PARTIAL")
    else:
        print(f"{Fore.RED}✗ Answer: {quality}")
    
    # Notes
    if result['notes']:
        print(f"{Fore.YELLOW}Notes:")
        for note in result['notes']:
            print(f"  - {note}")
    
    # Answer preview
    answer_preview = result['actual_answer'][:200] + "..." if len(result['actual_answer']) > 200 else result['actual_answer']
    print(f"{Fore.WHITE}Answer preview: {answer_preview}")


def print_summary(results: List[Dict]):
    """Print test summary."""
    total = len(results)
    source_correct = sum(1 for r in results if r['source_match'])
    answer_good = sum(1 for r in results if r['answer_quality'] == "GOOD")
    answer_partial = sum(1 for r in results if r['answer_quality'] == "PARTIAL")
    
    print(f"\n{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests: {total}")
    print(f"{Fore.GREEN}Source accuracy: {source_correct}/{total} ({source_correct/total*100:.1f}%)")
    print(f"{Fore.GREEN}Answer quality (GOOD): {answer_good}/{total} ({answer_good/total*100:.1f}%)")
    print(f"{Fore.YELLOW}Answer quality (PARTIAL): {answer_partial}/{total} ({answer_partial/total*100:.1f}%)")
    
    # Pass/fail criteria
    pass_threshold = 0.7  # 70% accuracy
    source_pass = source_correct / total >= pass_threshold
    # Consider both GOOD and PARTIAL as acceptable (PARTIAL gets warning but still passes)
    answer_acceptable = answer_good + answer_partial
    answer_pass = answer_acceptable / total >= pass_threshold
    
    if source_pass and answer_pass:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ TESTS PASSED")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}✗ TESTS FAILED")
        if not source_pass:
            print(f"{Fore.RED}  - Source accuracy below {pass_threshold*100}%")
        if not answer_pass:
            print(f"{Fore.RED}  - Answer quality (GOOD+PARTIAL) below {pass_threshold*100}%")


def main():
    """Run accuracy tests."""
    print(f"{Fore.CYAN}{Style.BRIGHT}SUBU Chatbot Accuracy Test")
    print(f"{'='*80}\n")
    
    # Load test questions
    try:
        questions = load_test_questions()
        print(f"Loaded {len(questions)} test questions\n")
    except FileNotFoundError:
        print(f"{Fore.RED}Error: test_questions.json not found!")
        return
    
    # Initialize chatbot
    print("Initializing chatbot...")
    generator = ResponseGenerator()
    print(f"{Fore.GREEN}✓ Chatbot ready\n")
    
    # Run tests
    results = []
    for i, question in enumerate(questions, 1):
        print(f"{Fore.CYAN}Running test {i}/{len(questions)}...", end='\r')
        
        # Get chatbot response
        response = generator.generate_response(question['question'])
        
        # Evaluate
        result = evaluate_response(question, response)
        results.append(result)
        
        # Print result
        print_result(result)
    
    # Print summary
    print_summary(results)
    
    # Save results to JSON
    output_file = "test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n{Fore.CYAN}Results saved to: {output_file}")


if __name__ == "__main__":
    main()
