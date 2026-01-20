"""Demo script to showcase the AI Account Coding Engine with 5 real examples.

This script demonstrates:
- Top 3 suggestions per line item
- Confidence scores for each suggestion
- Explanations for why each account was suggested
- Using the full LLM-powered pipeline
"""
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from src.core.engine import AccountCodingEngine
from src.utils.config import Settings


def format_suggestion(idx, sugg):
    """Format a single suggestion for display."""
    return f"""
    #{idx}:
      Account: {sugg.get('account', 'N/A')}
      Confidence: {sugg.get('confidence', 0.0):.1%}
      Explanation: {sugg.get('explanation', 'N/A')}
"""


def process_example(engine, invoice_text, description="Example"):
    """Process a single line item and display results."""
    print(f"\n{'='*80}")
    print(f"📋 {description}")
    print(f"{'='*80}")
    print(f"Input: {invoice_text}")
    print(f"-"*80)
    
    # Get suggestions
    result = engine.suggest_accounts(
        invoice_text=invoice_text,
        top_k=3
    )
    
    suggestions = result.get('suggestions', [])
    
    if not suggestions:
        print("❌ No suggestions generated")
        return
    
    print(f"\n🎯 Top 3 Suggestions:\n")
    for idx, sugg in enumerate(suggestions, 1):
        print(format_suggestion(idx, sugg))
    
    # Show classification metadata
    semantic_category = result.get('semantic_category', 'Unknown')
    classification_method = result.get('classification_method', 'Unknown')
    classification_confidence = result.get('classification_confidence', 0.0)
    
    print(f"\n📊 Classification Details:")
    print(f"  Category: {semantic_category}")
    print(f"  Method: {classification_method}")
    print(f"  Overall Confidence: {classification_confidence:.1%}")


def main():
    print("\n" + "="*80)
    print("🤖 AI Account Coding Engine - Demo with 5 Examples")
    print("="*80)
    
    # Initialize Azure OpenAI client
    azure_client = None
    try:
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if azure_endpoint and azure_key:
            azure_client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version=azure_version
            )
            print("✅ Azure OpenAI connected successfully\n")
        else:
            print("⚠️  Azure OpenAI credentials not found, using rule-based only\n")
    except Exception as e:
        print(f"⚠️  Could not connect to Azure OpenAI: {e}\n")
    
    # Initialize engine
    engine = AccountCodingEngine(azure_openai_client=azure_client)
    
    # 5 diverse examples showcasing different categories
    examples = [
        {
            "text": "Streng duct PP-HM Sickerrohr SN4 Ø150mm L5m",
            "desc": "Material (Pipes & Fittings)"
        },
        {
            "text": "Transportkosten per LKW nach Zürich",
            "desc": "Transport Costs"
        },
        {
            "text": "Energiezuschlag Januar 2026",
            "desc": "Surcharge (Energy)"
        },
        {
            "text": "Beratungsleistung Engineering für Statikberechnung",
            "desc": "External Service (Consulting)"
        },
        {
            "text": "Rapido Drahtbinder geschweisst 12cm 1000St.",
            "desc": "Consumables (Wire Ties)"
        }
    ]
    
    # Process each example
    for ex in examples:
        process_example(engine, ex["text"], ex["desc"])
    
    # Save results to file for reference
    output = {
        "demo_timestamp": "2026-01-19",
        "examples_processed": len(examples),
        "description": "Demo showing top 3 suggestions with confidence and explanations",
        "examples": []
    }
    
    for ex in examples:
        result = engine.suggest_accounts(invoice_text=ex["text"], top_k=3)
        output["examples"].append({
            "input": ex["text"],
            "description": ex["desc"],
            "suggestions": result.get('suggestions', []),
            "metadata": {
                "semantic_category": result.get('semantic_category'),
                "classification_method": result.get('classification_method'),
                "classification_confidence": result.get('classification_confidence')
            }
        })
    
    output_path = Path(__file__).parent.parent / "deliverables" / "milestone1" / "demo_5_examples.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ Demo complete! Results saved to: {output_path}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
