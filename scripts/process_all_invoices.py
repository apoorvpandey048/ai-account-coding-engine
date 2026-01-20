"""
Process all invoice items from all_Invoice_fields.json with real GL accounts.
Includes vendor-based 1:1 mapping and comprehensive metrics.
"""
import json
import csv
import sys
import os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from openai import AzureOpenAI

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.core.engine import AccountCodingEngine

def initialize_azure_client():
    """Initialize Azure OpenAI client"""
    try:
        # Check for Azure OpenAI credentials with both key names
        api_key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        if api_key and endpoint:
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            print(f"✓ Azure OpenAI client initialized")
            return client
        else:
            print("⚠ Azure OpenAI credentials not found, using rule-based only")
            return None
    except Exception as e:
        print(f"⚠ Failed to initialize Azure OpenAI: {e}")
        return None

# Load real chart of accounts
def load_kontoplan(filepath="data/Kontoplan.csv"):
    """Load the real chart of accounts from Kontoplan.csv"""
    accounts = {}
    # Try different encodings
    for encoding in ['latin-1', 'cp1252', 'iso-8859-1', 'utf-8']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if len(row) >= 2:
                        code = row[0].strip()
                        name = row[1].strip().strip("'")
                        accounts[code] = name
            print(f"Successfully loaded Kontoplan with {encoding} encoding")
            return accounts
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filepath} with any common encoding")

# Enhanced category to GL account mapping (real accounts)
CATEGORY_TO_GL_MAPPING = {
    "Raw Materials": [
        {"code": "1220", "name": "Materialvorräte", "confidence": 0.95},
        {"code": "1270", "name": "Angefangene Arbeiten", "confidence": 0.75}
    ],
    "Consumables": [
        {"code": "1220", "name": "Materialvorräte", "confidence": 0.90},
        {"code": "1540", "name": "Werkzeuge und Geräte", "confidence": 0.70}
    ],
    "Transport": [
        {"code": "4061", "name": "Fremdtransporte", "confidence": 0.95},
        {"code": "4062", "name": "Deponiegeb��hren", "confidence": 0.70}
    ],
    "Pallets": [
        {"code": "4010", "name": "Paletten Einkauf", "confidence": 0.95},
        {"code": "4011", "name": "Paletten Retouren", "confidence": 0.85}
    ],
    "Machinery & Equipment": [
        {"code": "1500", "name": "Maschinen und Apparate", "confidence": 0.95},
        {"code": "1540", "name": "Werkzeuge und Geräte", "confidence": 0.85}
    ],
    "Vehicles": [
        {"code": "1530", "name": "Fahrzeuge", "confidence": 0.95},
        {"code": "1531", "name": "Lieferwagen", "confidence": 0.90}
    ],
    "Buildings & Infrastructure": [
        {"code": "1600", "name": "Geschäftsliegenschaften", "confidence": 0.90}
    ],
    "IT & Office Equipment": [
        {"code": "1521", "name": "Informatik", "confidence": 0.95},
        {"code": "1520", "name": "Büromaschinen", "confidence": 0.90},
        {"code": "1510", "name": "Mobiliar und Einrichtungen", "confidence": 0.85}
    ],
    "Services": [
        {"code": "2004", "name": "Verbindlichkeiten übr. Betriebsaufwand", "confidence": 0.80},
        {"code": "2000", "name": "Verbindlichkeiten aus L+L", "confidence": 0.75}
    ]
}

# Vendor-based 1:1 mapping (Art-Nr -> specific GL account)
VENDOR_MAPPING = {
    "500000053": {"code": "4010", "name": "Paletten Einkauf", "confidence": 1.0, "reason": "Known pallet vendor code"},
    "200000036": {"code": "4061", "name": "Fremdtransporte", "confidence": 1.0, "reason": "Transport costs vendor code"},
    "200000028": {"code": "2004", "name": "Verbindlichkeiten übr. Betriebsaufwand", "confidence": 1.0, "reason": "Energy surcharge"},
    "200000026": {"code": "2004", "name": "Verbindlichkeiten übr. Betriebsaufwand", "confidence": 1.0, "reason": "Small quantity surcharge"}
}

def apply_vendor_mapping(item):
    """Check if item has a vendor-based 1:1 mapping"""
    art_nr = item.get("Art-Nr", "")
    if art_nr in VENDOR_MAPPING:
        mapping = VENDOR_MAPPING[art_nr]
        return {
            "account_code": mapping["code"],
            "account_name": mapping["name"],
            "confidence": mapping["confidence"],
            "method": "vendor_1to1",
            "reason": mapping["reason"]
        }
    return None

def map_category_to_gl(category, confidence):
    """Map semantic category to real GL account codes"""
    if category not in CATEGORY_TO_GL_MAPPING:
        return []
    
    gl_accounts = CATEGORY_TO_GL_MAPPING[category]
    results = []
    
    for gl in gl_accounts:
        # Adjust confidence based on original category confidence
        adjusted_conf = gl["confidence"] * confidence
        results.append({
            "account_code": gl["code"],
            "account_name": gl["name"],
            "confidence": round(adjusted_conf, 2),
            "method": "semantic_category",
            "category": category
        })
    
    return results

def process_all_items():
    """Process all items from all_Invoice_fields.json"""
    print("Loading all invoice items...")
    
    # Load all invoice data
    with open("3_examples/all_Invoice_fields.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)
    
    # Load Kontoplan
    kontoplan = load_kontoplan()
    print(f"Loaded {len(kontoplan)} GL accounts from Kontoplan")
    
    # Initialize Azure client and engine
    azure_client = initialize_azure_client()
    engine = AccountCodingEngine(azure_openai_client=azure_client)
    
    # Process all items
    all_results = []
    stats = {
        "total_items": 0,
        "vendor_mapped": 0,
        "semantic_mapped": 0,
        "method_breakdown": Counter(),
        "category_breakdown": Counter(),
        "gl_account_usage": Counter(),
        "confidence_distribution": defaultdict(int)
    }
    # Collect candidates by Pos (invoice position) to build Pos -> account mappings
    pos_candidates = defaultdict(list)
    
    for invoice_file, invoice_data in all_data.items():
        if "Fields" not in invoice_data or "Artikel" not in invoice_data["Fields"]:
            continue
        
        items = invoice_data["Fields"]["Artikel"]
        print(f"\nProcessing {invoice_file}: {len(items)} items")
        
        for idx, item in enumerate(items, 1):
            stats["total_items"] += 1
            pos = item.get("Pos", "")
            
            # Check vendor-based mapping first
            vendor_result = apply_vendor_mapping(item)
            
            if vendor_result:
                # Use vendor-based 1:1 mapping
                stats["vendor_mapped"] += 1
                stats["method_breakdown"]["vendor_1to1"] += 1
                stats["gl_account_usage"][vendor_result["account_code"]] += 1
                
                result = {
                    "invoice_file": invoice_file,
                    "item_number": idx,
                    "pos": pos,
                    "description": item.get("Bezeichnung", ""),
                    "art_nr": item.get("Art-Nr", ""),
                    "amount": item.get("Betrag", ""),
                    "mapping_method": "vendor_1to1",
                    "primary_account": vendor_result,
                    "alternative_accounts": []
                }
                # record pos candidate
                if pos:
                    pos_candidates[pos].append({
                        "account_code": vendor_result["account_code"],
                        "confidence": vendor_result.get("confidence", 1.0),
                        "method": "vendor_1to1"
                    })
            else:
                # Use semantic classification
                stats["semantic_mapped"] += 1
                
                # Get semantic suggestions from engine
                description = item.get("Bezeichnung", "")
                if not description:
                    stats["method_breakdown"]["unmapped"] += 1
                    result = {
                        "invoice_file": invoice_file,
                            "item_number": idx,
                            "pos": pos,
                        "description": description,
                        "art_nr": item.get("Art-Nr", ""),
                        "amount": item.get("Betrag", ""),
                        "mapping_method": "unmapped",
                        "primary_account": None,
                        "alternative_accounts": []
                    }
                else:
                    engine_result = engine.suggest_accounts(description, top_k=3)
                    
                    # Extract from engine response
                    primary_category = engine_result.get("semantic_category", "Unknown")
                    primary_confidence = engine_result.get("classification_confidence", 0.5)
                    primary_method = engine_result.get("classification_method", "unknown")
                    suggestions = engine_result.get("suggestions", [])
                    
                    stats["method_breakdown"][primary_method] += 1
                    stats["category_breakdown"][primary_category] += 1
                    
                    if suggestions and len(suggestions) > 0:
                        # Use the engine's suggestions directly (they already have real GL accounts)
                        primary_account = suggestions[0]["account"]
                        
                        # Extract code from account string (format: "CODE – Name")
                        account_code = primary_account.split("–")[0].strip() if "–" in primary_account else primary_account.split()[0]
                        stats["gl_account_usage"][account_code] += 1
                        
                        # Confidence bucket
                        conf_bucket = f"{int(suggestions[0]['confidence'] * 10) * 10}%"
                        stats["confidence_distribution"][conf_bucket] += 1
                        
                        result = {
                            "invoice_file": invoice_file,
                            "item_number": idx,
                            "pos": pos,
                            "description": description,
                            "art_nr": item.get("Art-Nr", ""),
                            "amount": item.get("Betrag", ""),
                            "mapping_method": "semantic",
                            "semantic_category": primary_category,
                            "classification_method": primary_method,
                            "classification_confidence": primary_confidence,
                            "primary_account": {
                                "account": primary_account,
                                "confidence": suggestions[0]["confidence"],
                                "explanation": suggestions[0]["explanation"]
                            },
                            "alternative_accounts": [
                                {
                                    "account": sug["account"],
                                    "confidence": sug["confidence"],
                                    "explanation": sug["explanation"]
                                }
                                for sug in suggestions[1:]
                            ] if len(suggestions) > 1 else []
                        }
                        # record pos candidates from suggestions
                        if pos:
                            for sug in suggestions:
                                try:
                                    code = sug["account"].split("–")[0].strip() if "–" in sug["account"] else sug["account"].split()[0]
                                except Exception:
                                    code = sug.get("account", "")
                                pos_candidates[pos].append({
                                    "account_code": code,
                                    "confidence": sug.get("confidence", 0.0),
                                    "method": "semantic"
                                })
                    else:
                        stats["method_breakdown"]["unmapped"] += 1
                        result = {
                            "invoice_file": invoice_file,
                            "item_number": idx,
                            "description": description,
                            "art_nr": item.get("Art-Nr", ""),
                            "amount": item.get("Betrag", ""),
                            "mapping_method": "unmapped",
                            "semantic_category": primary_category,
                            "primary_account": None,
                            "alternative_accounts": []
                        }
            
            all_results.append(result)
    
    # Save detailed results
    output_file = "deliverables/milestone1/all_invoices_mapped.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_items": stats["total_items"],
                "kontoplan_accounts": len(kontoplan)
            },
            "statistics": {
                "vendor_mapped_items": stats["vendor_mapped"],
                "semantic_mapped_items": stats["semantic_mapped"],
                "mapping_rate": round(stats["vendor_mapped"] + stats["semantic_mapped"], 2) / stats["total_items"] if stats["total_items"] > 0 else 0,
                "method_breakdown": dict(stats["method_breakdown"]),
                "category_breakdown": dict(stats["category_breakdown"]),
                "gl_account_usage": dict(stats["gl_account_usage"]),
                "confidence_distribution": dict(stats["confidence_distribution"])
            },
            "results": all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Processed {stats['total_items']} items")
    print(f"📊 Results saved to {output_file}")
    # Build Pos -> account candidate summary and save separately
    pos_summary = {}
    for p, entries in pos_candidates.items():
        agg = defaultdict(list)
        for e in entries:
            agg[e["account_code"]].append(e.get("confidence", 0.0))
        candidates = []
        for code, confs in agg.items():
            avg_conf = round(sum(confs) / len(confs), 2) if confs else 0.0
            candidates.append({
                "account_code": code,
                "count": len(confs),
                "avg_confidence": avg_conf
            })
        candidates.sort(key=lambda x: (x["count"], x["avg_confidence"]), reverse=True)
        pos_summary[p] = {"candidates": candidates}

    pos_file = "deliverables/milestone1/pos_mappings.json"
    with open(pos_file, "w", encoding="utf-8") as pf:
        json.dump({"generated_at": datetime.now().isoformat(), "pos_mappings": pos_summary}, pf, indent=2, ensure_ascii=False)
    print(f"📌 Pos mappings saved to {pos_file}")

    return all_results, stats

if __name__ == "__main__":
    results, stats = process_all_items()
    
    # Print summary
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    print(f"Total Items: {stats['total_items']}")
    print(f"Vendor 1:1 Mapped: {stats['vendor_mapped']} ({stats['vendor_mapped']/stats['total_items']*100:.1f}%)")
    print(f"Semantic Mapped: {stats['semantic_mapped']} ({stats['semantic_mapped']/stats['total_items']*100:.1f}%)")
    print(f"\nMethod Breakdown:")
    for method, count in stats['method_breakdown'].most_common():
        print(f"  {method}: {count} ({count/stats['total_items']*100:.1f}%)")
    print(f"\nTop Categories:")
    for category, count in stats['category_breakdown'].most_common(5):
        print(f"  {category}: {count}")
    print(f"\nTop GL Accounts Used:")
    for account, count in stats['gl_account_usage'].most_common(10):
        print(f"  {account}: {count} items")
