"""Create proper train/test split and prepare for retraining."""
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('data/invoice_text_with_accounts.csv')
print(f"Total dataset: {len(df)} samples, {df['suggested_account'].nunique()} unique accounts\n")

# Check distribution
print("Account distribution:")
print(df['suggested_account'].value_counts())
print()

# Split 80/20
# Put single-sample account in training to avoid having it only in test
single_sample_accounts = df['suggested_account'].value_counts()[df['suggested_account'].value_counts() == 1].index.tolist()
print(f"Accounts with only 1 sample: {single_sample_accounts}")

# Separate single-sample rows
single_sample_df = df[df['suggested_account'].isin(single_sample_accounts)]
multi_sample_df = df[~df['suggested_account'].isin(single_sample_accounts)]

# Split multi-sample data 80/20
train_multi, test_multi = train_test_split(
    multi_sample_df,
    test_size=0.2,
    random_state=42
)

# Add single-sample accounts to training set
train_df = pd.concat([train_multi, single_sample_df], ignore_index=True)
test_df = test_multi

print(f"\nSplit results:")
print(f"  Training: {len(train_df)} samples ({len(train_df)/len(df)*100:.1f}%)")
print(f"  Test: {len(test_df)} samples ({len(test_df)/len(df)*100:.1f}%)")

print(f"\nTraining set accounts: {train_df['suggested_account'].nunique()}")
print(f"Test set accounts: {test_df['suggested_account'].nunique()}")

# Save splits
train_df.to_csv('data/train_split.csv', index=False)
test_df.to_csv('data/test_split.csv', index=False)

print(f"\n✓ Saved:")
print(f"  data/train_split.csv ({len(train_df)} samples)")
print(f"  data/test_split.csv ({len(test_df)} samples)")

print(f"\n📝 Next steps:")
print(f"  1. Update gl_predictor.py to use train_split.csv")
print(f"  2. Restart the API to reload with training data only")
print(f"  3. Run evaluation on test_split.csv")
