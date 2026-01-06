import pandas as pd

df = pd.read_csv('data/invoice_text_with_accounts.csv')

print("="*70)
print("DATASET ANALYSIS")
print("="*70)
print(f"\nTotal samples: {len(df)}")
print(f"Unique accounts: {df['suggested_account'].nunique()}")
print(f"Samples per account (avg): {len(df)/df['suggested_account'].nunique():.1f}")

print("\n" + "="*70)
print("ACCOUNT DISTRIBUTION")
print("="*70)
account_dist = df['suggested_account'].value_counts()
print(account_dist.to_string())

print("\n" + "="*70)
print("ACCOUNTS WITH ONLY 1 SAMPLE")
print("="*70)
single_sample = account_dist[account_dist == 1]
if len(single_sample) > 0:
    print(f"Found {len(single_sample)} accounts with only 1 sample:")
    for acc in single_sample.index:
        print(f"  - {acc}")
else:
    print("None - all accounts have multiple samples")

print("\n" + "="*70)
print("TRAIN/TEST SPLIT FEASIBILITY")
print("="*70)
print(f"With 20% test split: ~{int(len(df)*0.2)} test samples, ~{int(len(df)*0.8)} train samples")
print(f"\nRecommendation:")
if len(df) < 100:
    print("  ⚠️  Dataset is small (< 100 samples)")
    print("  → Consider k-fold cross-validation (e.g., 5-fold) instead of single split")
    print("  → Or use larger test split (30-40%) if client provides more data")
if len(single_sample) > 0:
    print(f"  ⚠️  {len(single_sample)} accounts have only 1 sample")
    print("  → These accounts may not appear in both train and test")
    print("  → Cannot use stratified split")
print("\n" + "="*70)
