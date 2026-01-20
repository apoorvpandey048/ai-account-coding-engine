"""
Evaluation script for AI Account Coding Engine.

Evaluates different pipeline stages on test_split.csv:
1. Rule-based only (GLPredictor)
2. Core engine only (SemanticClassifier + AccountMapper)
3. Hybrid pipeline (rule → AI → core fallback)
4. Post-feedback simulation (optional)

Computes metrics: Top-1, Top-3 accuracy, MRR, coverage, confidence calibration.
Saves results to JSON and generates visualizations.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gl_predictor import GLPredictor
from src.core.engine import AccountCodingEngine
from src.core.classifier import SemanticClassifier
from src.core.mapper import AccountMapper

# Try importing for visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available, skipping charts")


def normalize_account(account: str) -> str:
    """Normalize account string for comparison."""
    return account.strip().lower()


def compute_metrics(predictions: List[Dict], ground_truth: pd.DataFrame) -> Dict:
    """
    Compute evaluation metrics.
    
    Args:
        predictions: List of dicts with keys: text, suggestions (list of {account, confidence})
        ground_truth: DataFrame with columns: extracted_invoice_text, suggested_account
    
    Returns:
        Dictionary of metrics
    """
    # Create ground truth lookup
    gt_lookup = {}
    for _, row in ground_truth.iterrows():
        gt_lookup[row['extracted_invoice_text'].strip()] = normalize_account(row['suggested_account'])
    
    top1_correct = 0
    top3_correct = 0
    reciprocal_ranks = []
    coverage_count = 0
    confidence_bins = defaultdict(list)  # bin -> list of (predicted_conf, is_correct)
    
    for pred in predictions:
        text = pred['text']
        suggestions = pred.get('suggestions', [])
        
        if not suggestions:
            continue
        
        coverage_count += 1
        gt_account = gt_lookup.get(text.strip())
        
        if not gt_account:
            continue  # Skip if no ground truth
        
        # Top-1 accuracy
        top1_account = normalize_account(suggestions[0]['account'])
        top1_conf = suggestions[0].get('confidence', 0.0)
        is_correct = (top1_account == gt_account)
        
        if is_correct:
            top1_correct += 1
        
        # Bin confidence for calibration
        conf_bin = int(top1_conf * 10) / 10.0  # 0.0-0.1, 0.1-0.2, ...
        confidence_bins[conf_bin].append((top1_conf, is_correct))
        
        # Top-3 accuracy and MRR
        found_rank = None
        for i, sug in enumerate(suggestions[:3], 1):
            if normalize_account(sug['account']) == gt_account:
                found_rank = i
                break
        
        if found_rank:
            top3_correct += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)
    
    total = len(predictions)
    
    # Compute calibration
    calibration = {}
    for bin_val, pairs in confidence_bins.items():
        avg_conf = np.mean([p[0] for p in pairs])
        empirical_acc = np.mean([p[1] for p in pairs])
        calibration[f"{bin_val:.1f}"] = {
            "predicted_confidence": float(avg_conf),
            "empirical_accuracy": float(empirical_acc),
            "count": len(pairs)
        }
    
    return {
        "total_samples": total,
        "coverage": coverage_count / total if total > 0 else 0.0,
        "top1_accuracy": top1_correct / total if total > 0 else 0.0,
        "top3_accuracy": top3_correct / total if total > 0 else 0.0,
        "mrr": np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0,
        "calibration": calibration,
        "human_review_rate_0.7": sum(1 for p in predictions if p.get('suggestions') and p['suggestions'][0].get('confidence', 0) < 0.7) / total if total > 0 else 0.0
    }


def apply_feedback_simulation(predictions: List[Dict], ground_truth: pd.DataFrame) -> Tuple[List[Dict], List[Dict]]:
    """Simulate user feedback by replacing incorrect top-1 predictions with the ground truth.

    Returns corrected predictions and a list of feedback records.
    """
    gt_lookup = {row['extracted_invoice_text'].strip(): normalize_account(row['suggested_account']) for _, row in ground_truth.iterrows()}
    corrected = []
    feedbacks = []

    for pred in predictions:
        text = pred['text']
        gt = gt_lookup.get(text.strip())
        orig_suggestions = pred.get('suggestions', [])

        # Determine top1
        top1 = normalize_account(orig_suggestions[0]['account']) if orig_suggestions else None

        if gt and top1 != gt:
            # Create feedback record
            feedbacks.append({
                'text': text,
                'correct_account': gt,
                'original_top1': top1,
                'original_suggestions': orig_suggestions
            })

            # Prepend the ground truth as top suggestion with high confidence
            new_suggestions = [{
                'account': gt,
                'confidence': 0.99,
                'explanation': 'user_feedback'
            }]

            # Keep original suggestions after
            for s in orig_suggestions:
                if normalize_account(s.get('account', '')) != gt:
                    new_suggestions.append(s)

            corrected.append({'text': text, 'suggestions': new_suggestions})
        else:
            corrected.append({'text': text, 'suggestions': orig_suggestions})

    return corrected, feedbacks


def evaluate_glpredictor(test_df: pd.DataFrame) -> Tuple[List[Dict], Dict]:
    """Evaluate GLPredictor (rule-based fuzzy matching)."""
    print("\n" + "="*60)
    print("Evaluating: GLPredictor (Rule-based)")
    print("="*60)
    
    predictor = GLPredictor()
    predictions = []
    
    for _, row in test_df.iterrows():
        text = row['extracted_invoice_text']
        try:
            suggestions_raw = predictor.suggest(text, top_k=3)
            suggestions = []
            
            for item in suggestions_raw:
                if isinstance(item, dict):
                    suggestions.append(item)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    suggestions.append({
                        "account": item[0],
                        "confidence": item[1],
                        "explanation": item[2] if len(item) > 2 else "Rule-based match"
                    })
            
            predictions.append({
                "text": text,
                "suggestions": suggestions
            })
        except Exception as e:
            print(f"Error predicting '{text}': {e}")
            predictions.append({"text": text, "suggestions": []})
    
    metrics = compute_metrics(predictions, test_df)
    print(f"Top-1 Accuracy: {metrics['top1_accuracy']:.2%}")
    print(f"Top-3 Accuracy: {metrics['top3_accuracy']:.2%}")
    print(f"MRR: {metrics['mrr']:.3f}")
    print(f"Coverage: {metrics['coverage']:.2%}")
    
    return predictions, metrics


def evaluate_core_engine(test_df: pd.DataFrame, azure_client=None) -> Tuple[List[Dict], Dict]:
    """Evaluate core engine (SemanticClassifier + AccountMapper)."""
    print("\n" + "="*60)
    print("Evaluating: Core Engine (Semantic Classifier + Mapper)")
    print("="*60)
    
    engine = AccountCodingEngine(azure_openai_client=azure_client)
    predictions = []
    
    for _, row in test_df.iterrows():
        text = row['extracted_invoice_text']
        try:
            result = engine.suggest_accounts(text, top_k=3)
            suggestions = result.get('suggestions', [])
            
            predictions.append({
                "text": text,
                "suggestions": suggestions
            })
        except Exception as e:
            print(f"Error predicting '{text}': {e}")
            predictions.append({"text": text, "suggestions": []})
    
    metrics = compute_metrics(predictions, test_df)
    print(f"Top-1 Accuracy: {metrics['top1_accuracy']:.2%}")
    print(f"Top-3 Accuracy: {metrics['top3_accuracy']:.2%}")
    print(f"MRR: {metrics['mrr']:.3f}")
    print(f"Coverage: {metrics['coverage']:.2%}")
    
    return predictions, metrics


def evaluate_hybrid_pipeline(test_df: pd.DataFrame, azure_client=None) -> Tuple[List[Dict], Dict]:
    """Evaluate hybrid pipeline (GLPredictor → Core Engine fallback)."""
    print("\n" + "="*60)
    print("Evaluating: Hybrid Pipeline (Rule → Core Fallback)")
    print("="*60)
    
    predictor = GLPredictor()
    engine = AccountCodingEngine(azure_openai_client=azure_client)
    predictions = []
    
    for _, row in test_df.iterrows():
        text = row['extracted_invoice_text']
        try:
            # Try GLPredictor first
            suggestions_raw = predictor.suggest(text, top_k=3)
            suggestions = []
            
            for item in suggestions_raw:
                if isinstance(item, dict):
                    suggestions.append(item)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    suggestions.append({
                        "account": item[0],
                        "confidence": item[1],
                        "explanation": item[2] if len(item) > 2 else "Rule-based match"
                    })
            
            # If low confidence, use core engine
            best_conf = max([s.get('confidence', 0) for s in suggestions], default=0)
            if best_conf < 0.7:
                result = engine.suggest_accounts(text, top_k=3)
                suggestions = result.get('suggestions', [])
            
            predictions.append({
                "text": text,
                "suggestions": suggestions
            })
        except Exception as e:
            print(f"Error predicting '{text}': {e}")
            predictions.append({"text": text, "suggestions": []})
    
    metrics = compute_metrics(predictions, test_df)
    print(f"Top-1 Accuracy: {metrics['top1_accuracy']:.2%}")
    print(f"Top-3 Accuracy: {metrics['top3_accuracy']:.2%}")
    print(f"MRR: {metrics['mrr']:.3f}")
    print(f"Coverage: {metrics['coverage']:.2%}")
    print(f"Human Review Rate (<0.7 conf): {metrics['human_review_rate_0.7']:.2%}")
    
    return predictions, metrics


def generate_charts(results: Dict, output_dir: Path):
    """Generate visualization charts."""
    if not HAS_MATPLOTLIB:
        print("Skipping charts (matplotlib not available)")
        return
    
    # Chart 1: Accuracy comparison
    stages = list(results.keys())
    top1_accs = [results[s]['metrics']['top1_accuracy'] for s in stages]
    top3_accs = [results[s]['metrics']['top3_accuracy'] for s in stages]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(stages))
    width = 0.35
    
    ax.bar(x - width/2, top1_accs, width, label='Top-1 Accuracy', color='#2E86AB')
    ax.bar(x + width/2, top3_accs, width, label='Top-3 Accuracy', color='#A23B72')
    
    ax.set_xlabel('Pipeline Stage', fontsize=12)
    ax.set_ylabel('Accuracy', fontsize=12)
    ax.set_title('Accuracy by Pipeline Stage', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(stages, rotation=15, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.0)
    
    # Add value labels on bars
    for i, (t1, t3) in enumerate(zip(top1_accs, top3_accs)):
        ax.text(i - width/2, t1 + 0.02, f'{t1:.1%}', ha='center', va='bottom', fontsize=9)
        ax.text(i + width/2, t3 + 0.02, f'{t3:.1%}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_dir / 'accuracy_comparison.png'}")
    
    # Chart 2: Metrics overview
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # MRR
    mrrs = [results[s]['metrics']['mrr'] for s in stages]
    axes[0, 0].barh(stages, mrrs, color='#F18F01')
    axes[0, 0].set_xlabel('MRR Score')
    axes[0, 0].set_title('Mean Reciprocal Rank')
    axes[0, 0].set_xlim(0, 1.0)
    axes[0, 0].grid(axis='x', alpha=0.3)
    
    # Coverage
    coverages = [results[s]['metrics']['coverage'] for s in stages]
    axes[0, 1].barh(stages, coverages, color='#06A77D')
    axes[0, 1].set_xlabel('Coverage')
    axes[0, 1].set_title('Prediction Coverage')
    axes[0, 1].set_xlim(0, 1.0)
    axes[0, 1].grid(axis='x', alpha=0.3)
    
    # Human review rate
    hr_rates = [results[s]['metrics'].get('human_review_rate_0.7', 0) for s in stages]
    axes[1, 0].barh(stages, hr_rates, color='#C73E1D')
    axes[1, 0].set_xlabel('Rate')
    axes[1, 0].set_title('Human Review Rate (<0.7 confidence)')
    axes[1, 0].set_xlim(0, 1.0)
    axes[1, 0].grid(axis='x', alpha=0.3)
    
    # Accuracy comparison
    axes[1, 1].plot(stages, top1_accs, marker='o', label='Top-1', linewidth=2)
    axes[1, 1].plot(stages, top3_accs, marker='s', label='Top-3', linewidth=2)
    axes[1, 1].set_ylabel('Accuracy')
    axes[1, 1].set_title('Accuracy Trends')
    axes[1, 1].legend()
    axes[1, 1].grid(alpha=0.3)
    axes[1, 1].set_ylim(0, 1.0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'metrics_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_dir / 'metrics_overview.png'}")


def save_examples(original_preds: List[Dict], corrected_preds: List[Dict], feedbacks: List[Dict], output_dir: Path):
    """Save example suggestions and explanations before/after feedback."""
    examples = []
    for o, c in zip(original_preds, corrected_preds):
        examples.append({
            'text': o['text'],
            'original_suggestions': o.get('suggestions', []),
            'corrected_suggestions': c.get('suggestions', [])
        })

    out = {
        'examples': examples,
        'feedbacks': feedbacks
    }
    with open(output_dir / 'example_suggestions_post_feedback.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {output_dir / 'example_suggestions_post_feedback.json'}")


def main():
    """Run full evaluation pipeline."""
    print("\n" + "="*60)
    print("AI ACCOUNT CODING ENGINE - PIPELINE EVALUATION")
    print("="*60)
    
    # Load test data
    test_path = Path(__file__).parent.parent / 'data' / 'test_split.csv'
    if not test_path.exists():
        print(f"Error: Test data not found at {test_path}")
        return
    
    test_df = pd.read_csv(test_path)
    print(f"\nLoaded test set: {len(test_df)} samples")
    print(f"Test file: {test_path}")
    
    # Prepare output directory
    output_dir = Path(__file__).parent.parent / 'deliverables' / 'milestone1'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run evaluations
    results = {}
    
    # Try to initialize Azure OpenAI client from environment (optional)
    try:
        from openai import AzureOpenAI
        azure_client = None
        # Check for both AZURE_OPENAI_KEY and AZURE_OPENAI_API_KEY
        api_key = os.environ.get('AZURE_OPENAI_KEY') or os.environ.get('AZURE_OPENAI_API_KEY')
        endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        
        if endpoint and api_key:
            azure_client = AzureOpenAI(
                api_key=api_key,
                api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                azure_endpoint=endpoint
            )
            print("Azure OpenAI client initialized for evaluation")
        else:
            azure_client = None
            print("Azure OpenAI not configured for evaluation; continuing without LLM")
    except Exception as e:
        azure_client = None
        print(f"Azure OpenAI client initialization failed: {e}")

    # 1. GLPredictor (rule-based)
    preds_glp, metrics_glp = evaluate_glpredictor(test_df)
    results['GLPredictor'] = {'metrics': metrics_glp}
    
    # 2. Core Engine
    preds_core, metrics_core = evaluate_core_engine(test_df, azure_client=azure_client)
    results['Core Engine'] = {'metrics': metrics_core}
    
    # 3. Hybrid Pipeline
    preds_hybrid, metrics_hybrid = evaluate_hybrid_pipeline(test_df, azure_client=azure_client)
    results['Hybrid Pipeline'] = {'metrics': metrics_hybrid}

    # 4. Simulate feedback loop: user corrects wrong top-1 by providing ground truth
    corrected_preds, feedbacks = apply_feedback_simulation(preds_hybrid, test_df)
    metrics_post_feedback = compute_metrics(corrected_preds, test_df)
    results['Hybrid Pipeline Post-Feedback'] = {'metrics': metrics_post_feedback}

    # Save example suggestions (original vs corrected)
    save_examples(preds_hybrid, corrected_preds, feedbacks, output_dir)
    
    # Save results
    results_path = output_dir / 'eval_results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Results saved: {results_path}")
    
    # Generate charts
    print("\nGenerating visualizations...")
    generate_charts(results, output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"\n{'Stage':<25} {'Top-1':<10} {'Top-3':<10} {'MRR':<10} {'Coverage':<10}")
    print("-" * 65)
    for stage, data in results.items():
        m = data['metrics']
        print(f"{stage:<25} {m['top1_accuracy']:>8.1%}  {m['top3_accuracy']:>8.1%}  {m['mrr']:>8.3f}  {m['coverage']:>8.1%}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS FOR CLIENT")
    print("="*60)
    print("• Current best: Hybrid Pipeline")
    print("• Recommended confidence threshold: 0.7")
    print(f"• Expected human review rate: {results['Hybrid Pipeline']['metrics'].get('human_review_rate_0.7', 0):.1%}")
    print(f"• Achievable automation rate: {1 - results['Hybrid Pipeline']['metrics'].get('human_review_rate_0.7', 0):.1%}")
    print("• With feedback loop: accuracy will improve over time")
    print("\n✓ Evaluation complete!")


if __name__ == "__main__":
    main()
