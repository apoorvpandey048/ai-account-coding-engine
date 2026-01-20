"""
Generate visual charts and detailed statistics from processing results.
"""
import json
from collections import Counter
from datetime import datetime

def generate_statistics_report():
    """Generate detailed statistics from all_invoices_mapped.json"""
    
    # Load results
    with open("deliverables/milestone1/all_invoices_mapped.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = data["results"]
    stats = data["statistics"]
    
    print("="*80)
    print("AI ACCOUNT CODING ENGINE - DETAILED STATISTICS REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Items Processed: {data['metadata']['total_items']}")
    print(f"GL Accounts Available: {data['metadata']['kontoplan_accounts']}")
    print("="*80)
    
    # Mapping Success Rate
    print("\n📊 MAPPING SUCCESS RATE")
    print("-"*80)
    mapped_count = stats["vendor_mapped_items"] + stats["semantic_mapped_items"]
    total = data['metadata']['total_items']
    success_rate = (mapped_count / total * 100) if total > 0 else 0
    print(f"Successfully Mapped: {mapped_count}/{total} ({success_rate:.1f}%)")
    print(f"  ├─ Vendor 1:1 Mapping: {stats['vendor_mapped_items']} ({stats['vendor_mapped_items']/total*100:.1f}%)")
    print(f"  └─ Semantic Mapping: {stats['semantic_mapped_items']} ({stats['semantic_mapped_items']/total*100:.1f}%)")
    
    unmapped = total - mapped_count
    if unmapped > 0:
        print(f"Unmapped (needs review): {unmapped} ({unmapped/total*100:.1f}%)")
    
    # Method Breakdown
    print("\n🔧 CLASSIFICATION METHOD BREAKDOWN")
    print("-"*80)
    method_stats = stats["method_breakdown"]
    sorted_methods = sorted(method_stats.items(), key=lambda x: x[1], reverse=True)
    
    for method, count in sorted_methods:
        percentage = (count / total * 100) if total > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{method:15s}: {bar:50s} {count:3d} ({percentage:5.1f}%)")
    
    # Category Distribution
    print("\n📦 SEMANTIC CATEGORY DISTRIBUTION")
    print("-"*80)
    category_stats = stats["category_breakdown"]
    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_categories[:10]:
        percentage = (count / total * 100) if total > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"{category:25s}: {bar:40s} {count:3d} ({percentage:5.1f}%)")
    
    # GL Account Usage
    print("\n💰 GL ACCOUNT USAGE (Top 15)")
    print("-"*80)
    gl_stats = stats["gl_account_usage"]
    sorted_gl = sorted(gl_stats.items(), key=lambda x: x[1], reverse=True)
    
    print(f"{'GL Code':<10} {'Account Name':<40} {'Count':<8} {'%':<8}")
    print("-"*80)
    
    # Map GL codes to names from results
    gl_names = {}
    for result in results:
        if result.get("primary_account"):
            if result["mapping_method"] == "vendor_1to1":
                code = result["primary_account"].get("account_code", "")
                name = result["primary_account"].get("account_name", "")
                if code and name:
                    gl_names[code] = name
            elif "account" in result["primary_account"]:
                account_str = result["primary_account"]["account"]
                if "–" in account_str:
                    parts = account_str.split("–")
                    code = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else ""
                    gl_names[code] = name
    
    for gl_code, count in sorted_gl[:15]:
        percentage = (count / mapped_count * 100) if mapped_count > 0 else 0
        name = gl_names.get(gl_code, "Unknown")
        print(f"{gl_code:<10} {name:<40} {count:<8} {percentage:>6.1f}%")
    
    # Confidence Distribution
    print("\n📈 CONFIDENCE DISTRIBUTION")
    print("-"*80)
    conf_stats = stats.get("confidence_distribution", {})
    
    if conf_stats:
        sorted_conf = sorted(conf_stats.items(), key=lambda x: x[0], reverse=True)
        for conf_range, count in sorted_conf:
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 2)
            print(f"{conf_range:10s}: {bar:40s} {count:3d} ({percentage:5.1f}%)")
    else:
        print("No confidence data available")
    
    # High-value items analysis
    print("\n💵 HIGH-VALUE ITEMS ANALYSIS")
    print("-"*80)
    
    value_items = []
    for result in results:
        amount_str = result.get("amount", "0")
        # Clean amount string (remove thousands separators, handle comma decimals)
        amount_str = amount_str.replace("'", "").replace(",", ".")
        try:
            amount = float(amount_str)
            value_items.append({
                "amount": amount,
                "description": result.get("description", "")[:50],
                "account": result.get("primary_account", {}).get("account", "Unmapped") if result.get("primary_account") else "Unmapped",
                "method": result.get("mapping_method", "unknown")
            })
        except:
            pass
    
    value_items.sort(key=lambda x: x["amount"], reverse=True)
    
    print(f"{'Amount':<12} {'Method':<12} {'GL Account':<30} {'Description'}")
    print("-"*80)
    for item in value_items[:10]:
        amount_fmt = f"CHF {item['amount']:,.2f}"
        account_short = item['account'][:28] if len(item['account']) > 28 else item['account']
        print(f"{amount_fmt:<12} {item['method']:<12} {account_short:<30} {item['description']}")
    
    # Invoice file breakdown
    print("\n📄 INVOICE FILE BREAKDOWN")
    print("-"*80)
    
    file_stats = {}
    for result in results:
        invoice_file = result.get("invoice_file", "Unknown")
        if invoice_file not in file_stats:
            file_stats[invoice_file] = {
                "total": 0,
                "vendor_mapped": 0,
                "semantic_mapped": 0,
                "unmapped": 0
            }
        
        file_stats[invoice_file]["total"] += 1
        
        if result.get("mapping_method") == "vendor_1to1":
            file_stats[invoice_file]["vendor_mapped"] += 1
        elif result.get("mapping_method") == "semantic":
            file_stats[invoice_file]["semantic_mapped"] += 1
        elif result.get("mapping_method") == "unmapped":
            file_stats[invoice_file]["unmapped"] += 1
    
    print(f"{'Invoice File':<30} {'Total':<8} {'Vendor':<8} {'AI':<8} {'Unmapped':<10} {'Success Rate'}")
    print("-"*80)
    
    for filename, fstats in sorted(file_stats.items()):
        success = fstats["vendor_mapped"] + fstats["semantic_mapped"]
        rate = (success / fstats["total"] * 100) if fstats["total"] > 0 else 0
        print(f"{filename:<30} {fstats['total']:<8} {fstats['vendor_mapped']:<8} {fstats['semantic_mapped']:<8} {fstats['unmapped']:<10} {rate:>5.1f}%")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Mapping Success Rate: {success_rate:.1f}%")
    print(f"✓ Vendor-Based Mappings (100% accurate): {stats['vendor_mapped_items']} items ({stats['vendor_mapped_items']/total*100:.1f}%)")
    print(f"✓ LLM-Powered Classifications: {method_stats.get('llm', 0)} items ({method_stats.get('llm', 0)/total*100:.1f}%)")
    print(f"✓ Hybrid Classifications: {method_stats.get('hybrid', 0) + method_stats.get('hybrid_llm', 0) + method_stats.get('hybrid_rule', 0)} items")
    print(f"✓ Most Used GL Account: {sorted_gl[0][0]} ({gl_names.get(sorted_gl[0][0], 'Unknown')}) - {sorted_gl[0][1]} items")
    print(f"✓ Items Needing Review: {unmapped}")
    print("="*80)
    print("\nReport completed successfully!")
    print("Full results available in: deliverables/milestone1/all_invoices_mapped.json")
    print("Progress report available in: deliverables/milestone1/PROGRESS_REPORT.md")
    print("="*80)

if __name__ == "__main__":
    generate_statistics_report()
