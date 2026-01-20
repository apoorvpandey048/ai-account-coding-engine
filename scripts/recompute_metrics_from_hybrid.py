"""Recompute evaluation metrics from deliverables/milestone1/hybrid_report.csv
and update deliverables/milestone1/eval_results.json (Hybrid Pipeline section).
"""
import csv
import json
from pathlib import Path
from statistics import mean
from collections import defaultdict


def normalize_account(a: str) -> str:
    return (a or "").strip().lower()


def compute_from_csv(csv_path: Path):
    rows = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    total = len(rows)
    if total == 0:
        raise SystemExit("No rows in hybrid report CSV")

    top1_correct = 0
    top3_correct = 0
    reciprocal_ranks = []
    confidence_bins = defaultdict(list)
    human_review_count = 0

    for r in rows:
        gt = normalize_account(r['ground_truth'])
        s_accounts = [normalize_account(r['s1_account']), normalize_account(r['s2_account']), normalize_account(r['s3_account'])]
        s_confs = [float(r['s1_confidence'] or 0), float(r['s2_confidence'] or 0), float(r['s3_confidence'] or 0)]

        # Top1
        if s_accounts[0] == gt:
            top1_correct += 1

        # Top3
        found_rank = None
        for i, acct in enumerate(s_accounts, start=1):
            if acct == gt:
                found_rank = i
                break
        if found_rank:
            top3_correct += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)

        # calibration bin on top1 confidence
        top1_conf = s_confs[0]
        bin_key = int(top1_conf * 10) / 10.0
        confidence_bins[bin_key].append((top1_conf, 1 if s_accounts[0] == gt else 0))

        if top1_conf < 0.7:
            human_review_count += 1

    calibration = {}
    for b, pairs in confidence_bins.items():
        avg_conf = mean([p[0] for p in pairs])
        emp_acc = mean([p[1] for p in pairs])
        calibration[f"{b:.1f}"] = {
            'predicted_confidence': round(avg_conf, 3),
            'empirical_accuracy': round(emp_acc, 3),
            'count': len(pairs)
        }

    metrics = {
        'total_samples': total,
        'coverage': 1.0,
        'top1_accuracy': round(top1_correct / total, 3),
        'top3_accuracy': round(top3_correct / total, 3),
        'mrr': round(mean(reciprocal_ranks), 3) if reciprocal_ranks else 0.0,
        'calibration': calibration,
        'human_review_rate_0.7': round(human_review_count / total, 3)
    }

    return metrics


def main():
    repo_root = Path(__file__).parent.parent
    csv_path = repo_root / 'deliverables' / 'milestone1' / 'hybrid_report.csv'
    eval_path = repo_root / 'deliverables' / 'milestone1' / 'eval_results.json'

    metrics = compute_from_csv(csv_path)

    # Load existing eval_results.json, update Hybrid Pipeline
    if eval_path.exists():
        with open(eval_path, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    data['Hybrid Pipeline'] = {'metrics': metrics}

    with open(eval_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print('Recomputed metrics and updated', eval_path)
    print(json.dumps({'Hybrid Pipeline': {'metrics': metrics}}, indent=2))


if __name__ == '__main__':
    main()
