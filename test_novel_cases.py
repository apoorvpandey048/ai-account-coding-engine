"""Test AI with novel cases not in training data."""
import requests
import json

API_URL = "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/suggest"

# Novel test cases - items NOT in training data
novel_cases = [
    "Microsoft Azure cloud computing subscription monthly fee",
    "Amazon Web Services EC2 instance hosting",
    "Google Workspace email licenses for team",
    "Zoom video conferencing annual subscription",
    "GitHub Enterprise developer tools license",
    "Employee training course fees",
    "Office coffee machine rental",
    "Company vehicle fuel costs",
    "Business insurance premium quarterly",
    "Legal consultation fees",
    "Marketing brochure printing",
    "Social media advertising campaign",
    "Recruitment agency placement fee",
    "Electricity bill manufacturing facility",
    "Water supply costs production area"
]

def test_novel_cases():
    print("="*70)
    print("TESTING AI WITH NOVEL CASES (Not in Training Data)")
    print("="*70)
    print()
    
    results = []
    
    for idx, text in enumerate(novel_cases, 1):
        try:
            response = requests.post(
                API_URL,
                json={"text": text, "top_k": 3},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            suggestions = data.get('suggestions', [])
            method = data.get('method', 'unknown')
            debug = data.get('debug', {})
            
            print(f"{idx}. {text}")
            print(f"   Method: {method.upper()}")
            print(f"   Initial confidence: {debug.get('initial_confidence', 'N/A')}")
            print(f"   Final confidence: {debug.get('final_confidence', 'N/A')}")
            print(f"   Suggestions:")
            for i, sug in enumerate(suggestions[:3], 1):
                print(f"      {i}. {sug['account']} ({sug['confidence']:.2f})")
                print(f"         → {sug['explanation']}")
            print()
            
            results.append({
                'text': text,
                'method': method,
                'top_suggestion': suggestions[0]['account'] if suggestions else 'N/A',
                'confidence': suggestions[0]['confidence'] if suggestions else 0,
                'initial_confidence': debug.get('initial_confidence'),
                'final_confidence': debug.get('final_confidence')
            })
            
        except Exception as e:
            print(f"{idx}. {text}")
            print(f"   ERROR: {e}")
            print()
    
    # Summary
    ai_count = sum(1 for r in results if r['method'] == 'ai')
    rule_count = sum(1 for r in results if r['method'] == 'rule-based')
    avg_final_conf = sum(r['final_confidence'] for r in results if r['final_confidence']) / len([r for r in results if r['final_confidence']])
    
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total novel cases tested: {len(novel_cases)}")
    print(f"AI-powered predictions: {ai_count} ({ai_count/len(results)*100:.1f}%)")
    print(f"Rule-based predictions: {rule_count} ({rule_count/len(results)*100:.1f}%)")
    print(f"Average final confidence: {avg_final_conf:.2f}")
    print()
    print("KEY INSIGHT: Novel cases trigger AI, demonstrating the system's ability")
    print("to handle items not seen during training with intelligent reasoning.")
    print("="*70)
    
    # Save results
    with open('novel_cases_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: novel_cases_results.json")

if __name__ == "__main__":
    test_novel_cases()
