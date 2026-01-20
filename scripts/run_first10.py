import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.engine import AccountCodingEngine

# Try to initialize AzureOpenAI client if available
azure_client = None
try:
    from openai import AzureOpenAI
    api_key = os.environ.get('AZURE_OPENAI_KEY') or os.environ.get('AZURE_OPENAI_API_KEY')
    endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
    if api_key and endpoint:
        azure_client = AzureOpenAI(api_key=api_key, api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'), azure_endpoint=endpoint)
        print('Azure OpenAI client initialized')
    else:
        print('Azure OpenAI not configured; running with rule-based only')
except Exception as e:
    print('AzureOpenAI import failed:', e)
    azure_client = None

engine = AccountCodingEngine(azure_openai_client=azure_client)

# Load example JSON
examples_path = Path(__file__).parent.parent / '3_examples' / 'all_Invoice_fields.json'
with open(examples_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Collect first 10 line items across files
items = []
for key in sorted(data.keys()):
    entry = data[key]
    artikel = entry.get('Fields', {}).get('Artikel', [])
    for a in artikel:
        items.append(a)
        if len(items) >= 10:
            break
    if len(items) >= 10:
        break

results = []
for idx, it in enumerate(items, 1):
    invoice_text = it.get('Bezeichnung') or it.get('designation') or ''
    supplier = it.get('Art-Nr')
    # parse numeric fields
    def parse_number(s):
        if s is None:
            return None
        try:
            return float(str(s).replace("'", '').replace(',', '').strip())
        except:
            try:
                return float(str(s).replace(',', '.').replace("'", ''))
            except:
                return None
    quantity = it.get('Anzahl')
    unit_price = parse_number(it.get('Preis'))
    line_amount = parse_number(it.get('Betrag'))

    res = engine.suggest_accounts(
        invoice_text=invoice_text,
        supplier=supplier,
        quantity=None,
        unit_of_measure=None,
        unit_price=unit_price,
        line_amount=line_amount,
        product_group=None,
        po_reference=None,
        top_k=3
    )
    results.append({
        'index': idx,
        'raw_item': it,
        'request': {'invoice_text': invoice_text, 'supplier': supplier, 'unit_price': unit_price, 'line_amount': line_amount},
        'result': res
    })
    print(f"Processed {idx}: {invoice_text[:60]!r} -> {res['suggestions'][0]['account']}")

# Save results
out_dir = Path('deliverables') / 'milestone1'
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / 'run_first10.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Saved {len(results)} results to {out_file}")
