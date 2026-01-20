"""Generate a human-friendly hybrid pipeline report.

For each sample in `data/test_split.csv` this script records:
- input text
- ground truth account
- up to 3 suggestions (account, confidence, explanation)
- `top1_correct` boolean
- `in_top3` boolean

Outputs:
- deliverables/milestone1/hybrid_report.json
- deliverables/milestone1/hybrid_report.csv
"""
import json
import csv
import sys
from pathlib import Path
import pandas as pd

# ensure repo root on path so we can import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from gl_predictor import GLPredictor
from src.core.engine import AccountCodingEngine


def normalize_account(a: str) -> str:
    return a.strip().lower() if a else ""


def to_suggestion(item):
    if isinstance(item, dict):
        return {
            'account': item.get('account'),
            'confidence': float(item.get('confidence', 0.0)),
            'explanation': item.get('explanation', '')
        }
    elif isinstance(item, (list, tuple)) and len(item) >= 2:
        return {
            'account': item[0],
            'confidence': float(item[1]),
            'explanation': item[2] if len(item) > 2 else ''
        }
    else:
        return {'account': None, 'confidence': 0.0, 'explanation': ''}


def run():
    repo_root = Path(__file__).parent.parent
    test_path = repo_root / 'data' / 'test_split.csv'
    out_dir = repo_root / 'deliverables' / 'milestone1'
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(test_path)
    predictor = GLPredictor()
    engine = AccountCodingEngine()

    rows = []

    for _, r in df.iterrows():
        text = r['extracted_invoice_text']
        gt = r['suggested_account']

        # GLPredictor first
        try:
            raw = predictor.suggest(text, top_k=5)
        except Exception:
            raw = []

        gl_suggestions = [to_suggestion(i) for i in raw]

        # Always call core engine to ensure we can merge and provide up to 3 unique suggestions
        try:
            res = engine.suggest_accounts(text, top_k=5)
            engine_suggestions = [to_suggestion(i) for i in res.get('suggestions', [])]
        except Exception:
            engine_suggestions = []

        # Merge suggestions: prefer GLPredictor order, then engine suggestions, deduplicate
        merged = []
        seen = set()

        def add_if_new(s):
            acct_norm = normalize_account(s.get('account') or '')
            if acct_norm and acct_norm not in seen:
                merged.append(s)
                seen.add(acct_norm)

        for s in gl_suggestions:
            add_if_new(s)
        for s in engine_suggestions:
            if len(merged) >= 3:
                break
            add_if_new(s)

        # If still fewer than 3, append a low-confidence 'Other' placeholder
        while len(merged) < 3:
            merged.append({'account': 'Other', 'confidence': 0.01, 'explanation': 'fallback_placeholder'})

        suggestions = merged[:3]

        # ensure three-slot list (may be shorter)
        while len(suggestions) < 3:
            suggestions.append({'account': None, 'confidence': 0.0, 'explanation': ''})

        top1 = normalize_account(suggestions[0]['account'] or '')
        gt_norm = normalize_account(gt)
        in_top3 = any(normalize_account(s['account'] or '') == gt_norm for s in suggestions)
        top1_correct = top1 == gt_norm

        row = {
            'text': text,
            'ground_truth': gt,
            'top1_correct': bool(top1_correct),
            'in_top3': bool(in_top3),
            'suggestions': suggestions
        }
        rows.append(row)

    # write JSON
    with open(out_dir / 'hybrid_report.json', 'w', encoding='utf-8') as jf:
        json.dump({'rows': rows}, jf, indent=2, ensure_ascii=False)

    # write CSV (flatten suggestions)
    csv_path = out_dir / 'hybrid_report.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as cf:
        writer = csv.writer(cf)
        header = [
            'text', 'ground_truth', 'top1_correct', 'in_top3',
            's1_account', 's1_confidence', 's1_explanation',
            's2_account', 's2_confidence', 's2_explanation',
            's3_account', 's3_confidence', 's3_explanation'
        ]
        writer.writerow(header)
        for r in rows:
            s = r['suggestions']
            writer.writerow([
                r['text'], r['ground_truth'], r['top1_correct'], r['in_top3'],
                s[0]['account'], s[0]['confidence'], s[0]['explanation'],
                s[1]['account'], s[1]['confidence'], s[1]['explanation'],
                s[2]['account'], s[2]['confidence'], s[2]['explanation']
            ])

    print(f"✓ Saved: {out_dir / 'hybrid_report.json'}")
    print(f"✓ Saved: {out_dir / 'hybrid_report.csv'}")


if __name__ == '__main__':
    run()
