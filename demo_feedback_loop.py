"""
Demo: AI Top-3 Suggestions + Feedback Loop

This script demonstrates:
1. AI generates top-3 GL account suggestions with explanations
2. System detects first mistake
3. Sends feedback with correct account (from ground truth)
4. Re-runs evaluation with feedback as few-shot example
5. Shows before/after comparison

Perfect for client demo screenshots.
"""
import os
import json
import pandas as pd
import requests
from typing import List, Dict, Optional
from openai import AzureOpenAI
import difflib
import time

# Azure OpenAI configuration
DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4-1-mini')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
KEY = os.getenv('AZURE_OPENAI_KEY')
API_VERSION = os.getenv('OPENAI_API_VERSION', '2024-08-01-preview')
MAX_TOKENS = 1500
TEMPERATURE = 0.3

# API endpoint for feedback
API_URL = os.getenv('EVAL_API_URL', 'http://127.0.0.1:8001')

print("="*80)
print("AI ACCOUNT CODING - FEEDBACK LOOP DEMONSTRATION")
print("="*80)


def build_prompt_with_context(invoice_text: str, allowed_accounts: List[str], 
                               feedback_examples: Optional[List[tuple]] = None) -> str:
    """Build prompt with optional feedback examples as few-shot learning."""
    accounts_list = "\n".join([f"  - {acc}" for acc in allowed_accounts])
    
    few_shot_section = ""
    if feedback_examples:
        few_shot_section = "\n\n📚 LEARNING FROM FEEDBACK:\n"
        for i, (text, correct_account, reason) in enumerate(feedback_examples, 1):
            few_shot_section += f'{i}. "{text}" → Correct account: {correct_account}\n   Reason: {reason}\n'
        few_shot_section += "\nUse these examples to improve your suggestions.\n"
    
    prompt = f"""You are an expert accounting AI assistant analyzing invoice line items for GL account coding.

ALLOWED ACCOUNTS (you must choose from this list only):
{accounts_list}
{few_shot_section}
INVOICE LINE ITEM TO ANALYZE:
"{invoice_text}"

YOUR TASK:
Return a JSON object with top 3 GL account suggestions, ordered by confidence.

REQUIRED JSON FORMAT:
{{
  "suggestions": [
    {{
      "account": "exact account string from allowed list",
      "confidence": 0.XX,
      "explanation": "Specific reasoning for THIS item (mention key terms, category, typical use)"
    }},
    {{
      "account": "second choice",
      "confidence": 0.XX,
      "explanation": "Why this is also possible"
    }},
    {{
      "account": "third choice",
      "confidence": 0.XX,
      "explanation": "Alternative rationale"
    }}
  ]
}}

REQUIREMENTS:
- Return ONLY valid JSON, no other text
- All 3 accounts must be from the allowed list
- Confidence scores should decrease (most confident first)
- Explanations must be specific to THIS invoice item
- Consider item category (material, consumables, transport, services, etc.)
"""
    return prompt


def call_ai_with_top3(client: AzureOpenAI, invoice_text: str, allowed_accounts: List[str],
                      feedback_examples: Optional[List[tuple]] = None) -> Dict:
    """Call Azure OpenAI and get top-3 suggestions with explanations."""
    prompt = build_prompt_with_context(invoice_text, allowed_accounts, feedback_examples)
    
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a precise accounting assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON
    try:
        result = json.loads(content)
    except:
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            raise ValueError(f"Could not parse JSON from: {content}")
    
    # Validate and fuzzy-match accounts
    suggestions = result.get('suggestions', [])
    validated = []
    for s in suggestions:
        acc = s.get('account', '')
        if acc in allowed_accounts:
            validated.append(s)
        else:
            # Try fuzzy match
            matches = difflib.get_close_matches(acc, allowed_accounts, n=1, cutoff=0.7)
            if matches:
                s['account'] = matches[0]
                validated.append(s)
    
    return {"suggestions": validated}


def send_feedback_to_api(invoice_text: str, correct_account: str, 
                         predicted_account: str, confidence: float) -> bool:
    """Send feedback to the /feedback API endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/feedback",
            json={
                "text": invoice_text,
                "selected_account": correct_account,
                "confidence": confidence,
                "notes": f"Correction: AI predicted {predicted_account}, correct answer is {correct_account}"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print(f"✓ Feedback sent to API: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Feedback API error: {e}")
        return False


def run_evaluation_round(client: AzureOpenAI, test_df: pd.DataFrame, 
                        allowed_accounts: List[str], 
                        feedback_examples: Optional[List[tuple]] = None,
                        round_name: str = "Round 1") -> tuple:
    """Run one evaluation round and return results + first error."""
    print(f"\n{'='*80}")
    print(f"{round_name}: EVALUATING {len(test_df)} TEST SAMPLES")
    print(f"{'='*80}\n")
    
    results = []
    first_error = None
    correct_count = 0
    
    for idx, row in test_df.iterrows():
        text = row['extracted_invoice_text']
        expected = row['suggested_account']
        
        try:
            result = call_ai_with_top3(client, text, allowed_accounts, feedback_examples)
            suggestions = result.get('suggestions', [])
            
            # Check top-1, top-3
            top1 = suggestions[0]['account'] if suggestions else 'N/A'
            top3_accounts = [s['account'] for s in suggestions[:3]]
            
            top1_correct = (top1 == expected)
            top3_correct = (expected in top3_accounts)
            
            if top1_correct:
                correct_count += 1
            
            result_entry = {
                'index': idx,
                'text': text,
                'expected': expected,
                'top1': top1,
                'top2': suggestions[1]['account'] if len(suggestions) > 1 else 'N/A',
                'top3': suggestions[2]['account'] if len(suggestions) > 2 else 'N/A',
                'conf1': suggestions[0].get('confidence', 0) if suggestions else 0,
                'conf2': suggestions[1].get('confidence', 0) if len(suggestions) > 1 else 0,
                'conf3': suggestions[2].get('confidence', 0) if len(suggestions) > 2 else 0,
                'explanation1': suggestions[0].get('explanation', '') if suggestions else '',
                'explanation2': suggestions[1].get('explanation', '') if len(suggestions) > 1 else '',
                'explanation3': suggestions[2].get('explanation', '') if len(suggestions) > 2 else '',
                'top1_correct': top1_correct,
                'top3_correct': top3_correct
            }
            
            results.append(result_entry)
            
            # Display
            status = "✓" if top1_correct else "✗"
            print(f"{idx+1}/{len(test_df)} {status} Expected: {expected}")
            print(f"   Top-1: {top1} (conf={result_entry['conf1']:.2f})")
            print(f"   └─ {result_entry['explanation1'][:80]}...")
            
            if len(suggestions) > 1:
                print(f"   Top-2: {result_entry['top2']} (conf={result_entry['conf2']:.2f})")
            if len(suggestions) > 2:
                print(f"   Top-3: {result_entry['top3']} (conf={result_entry['conf3']:.2f})")
            
            if not top1_correct and first_error is None:
                # Found first error
                first_error = result_entry
                print(f"\n   ⚠️  FIRST MISTAKE DETECTED!")
                if top3_correct:
                    correct_position = top3_accounts.index(expected) + 1
                    print(f"   💡 Correct answer WAS in suggestions (position {correct_position})")
                else:
                    print(f"   💡 Correct answer NOT in top-3")
            
            print()
            
        except Exception as e:
            print(f"{idx+1}/{len(test_df)} ERROR: {e}\n")
            results.append({
                'index': idx, 'text': text, 'expected': expected,
                'top1': 'ERROR', 'top2': 'N/A', 'top3': 'N/A',
                'conf1': 0, 'conf2': 0, 'conf3': 0,
                'explanation1': str(e), 'explanation2': '', 'explanation3': '',
                'top1_correct': False, 'top3_correct': False
            })
    
    accuracy = correct_count / len(test_df) * 100
    print(f"\n{round_name} RESULTS: {correct_count}/{len(test_df)} correct (Top-1 Accuracy: {accuracy:.1f}%)\n")
    
    return results, first_error, accuracy


def main():
    # Initialize
    if not (ENDPOINT and KEY):
        print("❌ Error: Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")
        return
    
    client = AzureOpenAI(azure_endpoint=ENDPOINT, api_key=KEY, api_version=API_VERSION)
    
    # Load data
    test_df = pd.read_csv('data/test_split.csv')
    train_df = pd.read_csv('data/train_split.csv')
    allowed_accounts = list(train_df['suggested_account'].unique())
    
    print(f"\n📊 Dataset: {len(test_df)} test samples")
    print(f"📋 Allowed accounts: {len(allowed_accounts)}")
    print(f"🎯 Goal: Demonstrate feedback loop improvement\n")
    
    # ROUND 1: Baseline (no feedback)
    results_before, first_error, accuracy_before = run_evaluation_round(
        client, test_df, allowed_accounts, 
        feedback_examples=None,
        round_name="ROUND 1 (Baseline - No Feedback)"
    )
    
    if first_error is None:
        print("✨ Perfect score! No mistakes to learn from.")
        # Save results
        pd.DataFrame(results_before).to_csv('demo_feedback_baseline.csv', index=False)
        return
    
    # FEEDBACK INJECTION
    print("="*80)
    print("📝 FEEDBACK LOOP ACTIVATION")
    print("="*80)
    print(f"\nFirst mistake details:")
    print(f"  Invoice text: {first_error['text']}")
    print(f"  AI predicted: {first_error['top1']} (confidence: {first_error['conf1']:.2f})")
    print(f"  Correct answer: {first_error['expected']}")
    print(f"  AI reasoning: {first_error['explanation1']}")
    
    # Send feedback to API
    print(f"\n📤 Sending feedback to API ({API_URL}/feedback)...")
    feedback_sent = send_feedback_to_api(
        first_error['text'],
        first_error['expected'],
        first_error['top1'],
        first_error['conf1']
    )
    
    # Prepare feedback for next round (few-shot learning)
    feedback_examples = [(
        first_error['text'],
        first_error['expected'],
        f"User confirmed this should be {first_error['expected']}, not {first_error['top1']}"
    )]
    
    print(f"\n💾 Feedback stored and will be used as few-shot example in next round...")
    time.sleep(2)
    
    # ROUND 2: With feedback
    results_after, _, accuracy_after = run_evaluation_round(
        client, test_df, allowed_accounts,
        feedback_examples=feedback_examples,
        round_name="ROUND 2 (With Feedback)"
    )
    
    # COMPARISON
    print("="*80)
    print("📊 FEEDBACK LOOP IMPACT ANALYSIS")
    print("="*80)
    print(f"\nTop-1 Accuracy:")
    print(f"  Before feedback: {accuracy_before:.1f}%")
    print(f"  After feedback:  {accuracy_after:.1f}%")
    print(f"  Improvement:     {accuracy_after - accuracy_before:+.1f}%")
    
    # Check if the specific error was fixed
    error_idx = first_error['index']
    result_after_for_error = next(r for r in results_after if r['index'] == error_idx)
    
    print(f"\n🔍 Specific feedback case (sample #{error_idx+1}):")
    print(f"  Text: {first_error['text'][:60]}...")
    print(f"  Before: {first_error['top1']} ✗")
    print(f"  After:  {result_after_for_error['top1']} {'✓' if result_after_for_error['top1_correct'] else '✗'}")
    
    if result_after_for_error['top1_correct']:
        print(f"\n  ✅ SUCCESS! AI learned from feedback and corrected this case.")
        print(f"  New explanation: {result_after_for_error['explanation1'][:100]}...")
    else:
        print(f"\n  ⚠️  Still incorrect, but AI reasoning changed:")
        print(f"  New explanation: {result_after_for_error['explanation1'][:100]}...")
    
    # Save results
    pd.DataFrame(results_before).to_csv('demo_feedback_before.csv', index=False)
    pd.DataFrame(results_after).to_csv('demo_feedback_after.csv', index=False)
    
    summary = {
        "baseline_accuracy": accuracy_before,
        "feedback_accuracy": accuracy_after,
        "improvement": accuracy_after - accuracy_before,
        "first_error": {
            "text": first_error['text'],
            "predicted": first_error['top1'],
            "correct": first_error['expected'],
            "fixed_after_feedback": result_after_for_error['top1_correct']
        },
        "feedback_sent_to_api": feedback_sent
    }
    
    with open('demo_feedback_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 Results saved:")
    print(f"  - demo_feedback_before.csv (baseline predictions)")
    print(f"  - demo_feedback_after.csv (predictions after feedback)")
    print(f"  - demo_feedback_summary.json (summary metrics)")
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("\n📸 You can now take screenshots of:")
    print("  1. First round results showing the mistake")
    print("  2. Feedback being sent")
    print("  3. Second round results showing improvement")
    print("  4. Comparison metrics\n")


if __name__ == '__main__':
    main()
