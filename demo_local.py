"""
Complete Local Demo Script for Vincent
=======================================
Processes all invoice items from all_Invoice_fields.json using:
- Real chart of accounts (Kontoplan.csv)
- Pos-based mapping prioritization
- Azure OpenAI LLM classification (when configured)

Outputs results in API response format with 3 suggestions per item.

Usage:
    python demo_local.py

Requirements:
    - Azure OpenAI credentials in .env (optional, falls back to rule-based)
    - Files: 3_examples/all_Invoice_fields.json, data/Kontoplan.csv
    - Generated pos_mappings.json (created automatically if missing)

Output:
    demo_results.json - Complete results for all invoice items
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

from src.core.engine import AccountCodingEngine


def initialize_azure_client():
    """Initialize Azure OpenAI client if credentials available."""
    try:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_KEY")
        version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        if endpoint and key:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=key,
                api_version=version
            )
            print("✅ Azure OpenAI connected")
            return client
        else:
            print("⚠️  Azure OpenAI not configured - using rule-based classification only")
            return None
    except Exception as e:
        print(f"⚠️  Could not connect to Azure OpenAI: {e}")
        return None


def load_invoice_data():
    """Load all invoice items from all_Invoice_fields.json."""
    file_path = Path("3_examples/all_Invoice_fields.json")
    if not file_path.exists():
        raise FileNotFoundError(f"Invoice data not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"✅ Loaded invoice data from {file_path}")
    return data


def process_all_items(engine, invoice_data):
    """Process all invoice items and return results in API format."""
    results = []
    total_items = 0
    
    for invoice_file, invoice_content in invoice_data.items():
        if "Fields" not in invoice_content or "Artikel" not in invoice_content["Fields"]:
            continue
        
        items = invoice_content["Fields"]["Artikel"]
        print(f"\n📄 Processing {invoice_file}: {len(items)} items")
        
        for idx, item in enumerate(items, 1):
            total_items += 1
            
            # Extract fields
            description = item.get("Bezeichnung", "").strip()
            pos = item.get("Pos", "")
            art_nr = item.get("Art-Nr", "")
            amount = item.get("Betrag", "")
            quantity = item.get("Anzahl", "")
            price = item.get("Preis", "")
            
            if not description:
                print(f"  ⚠️  Item {idx}: No description, skipping")
                continue
            
            # Call engine with Pos for prioritization
            try:
                result = engine.suggest_accounts(
                    invoice_text=description,
                    pos=pos,
                    line_amount=amount,
                    quantity=quantity,
                    top_k=3
                )
                
                # Build output in API response format
                output = {
                    "invoice_file": invoice_file,
                    "item_number": idx,
                    "pos": pos,
                    "art_nr": art_nr,
                    "description": description,
                    "amount": amount,
                    "quantity": quantity,
                    "price": price,
                    "suggestions": result["suggestions"],  # Already in correct format
                    "semantic_category": result["semantic_category"],
                    "classification_confidence": result["classification_confidence"],
                    "classification_method": result["classification_method"],
                    "classification_reasoning": result.get("classification_reasoning", ""),
                    "metadata": result["metadata"]
                }
                
                results.append(output)
                
                # Print summary
                top_account = result["suggestions"][0]["account"] if result["suggestions"] else "N/A"
                top_conf = result["suggestions"][0]["confidence"] if result["suggestions"] else 0
                print(f"  ✅ Item {idx} ({pos}): {description[:50]}... → {top_account} ({top_conf:.1%})")
                
            except Exception as e:
                print(f"  ❌ Item {idx}: Error - {e}")
                results.append({
                    "invoice_file": invoice_file,
                    "item_number": idx,
                    "pos": pos,
                    "art_nr": art_nr,
                    "description": description,
                    "error": str(e)
                })
    
    print(f"\n✅ Processed {total_items} items total")
    return results


def save_results(results):
    """Save results to demo_results.json."""
    output_file = Path("demo_results.json")
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_items": len(results),
        "description": "Complete demo results using all_Invoice_fields.json with Pos-based prioritization",
        "results": results
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {output_file.absolute()}")
    return output_file


def print_summary(results):
    """Print summary statistics."""
    total = len(results)
    errors = sum(1 for r in results if "error" in r)
    successful = total - errors
    
    if successful > 0:
        # Gather method breakdown
        methods = {}
        for r in results:
            if "classification_method" in r:
                method = r["classification_method"]
                methods[method] = methods.get(method, 0) + 1
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Items: {total}")
        print(f"Successful: {successful}")
        print(f"Errors: {errors}")
        print(f"\nClassification Methods:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            print(f"  {method}: {count} ({count/successful*100:.1f}%)")
        print("="*60)


def main():
    """Main execution."""
    print("\n" + "="*60)
    print("🤖 AI Account Coding - Complete Local Demo")
    print("="*60 + "\n")
    
    # Initialize Azure OpenAI client
    azure_client = initialize_azure_client()
    
    # Initialize engine (will load pos_mappings.json if available)
    engine = AccountCodingEngine(azure_openai_client=azure_client)
    
    # Load invoice data
    invoice_data = load_invoice_data()
    
    # Process all items
    results = process_all_items(engine, invoice_data)
    
    # Save results
    output_file = save_results(results)
    
    # Print summary
    print_summary(results)
    
    print(f"\n✅ Demo complete!")
    print(f"📊 View results: {output_file}")
    print("\nNext steps:")
    print("  - Review demo_results.json for accuracy")
    print("  - Check suggestions have 3 alternatives with confidence + explanations")
    print("  - Look for 'Pos signal' in explanations (Pos-prioritized suggestions)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
