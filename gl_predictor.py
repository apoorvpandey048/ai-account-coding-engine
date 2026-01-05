import pandas as pd
import re
from collections import Counter

class GLPredictor:
    """Simple rule-assisted GL predictor using the provided CSV mapping.

    By default it loads the sample CSV from the `data/` folder when available.
    """

    def __init__(self, mapping_csv=None):
        if mapping_csv is None:
            mapping_csv = 'data/invoice_text_with_accounts.csv'
        self.df = pd.read_csv(mapping_csv)
        # parse suggested_account into code and label if present
        self.df[['account_code','account_label']] = self.df['suggested_account'].str.split(' – ', n=1, expand=True)
        # build keyword index from invoice texts
        self.keyword_index = self._build_keyword_index()

    def _tokenize(self, text):
        text = text.lower()
        tokens = re.findall(r"[a-z0-9äöüß]+", text)
        return tokens

    def _build_keyword_index(self):
        index = {}
        for _, row in self.df.iterrows():
            tokens = set(self._tokenize(row['extracted_invoice_text']))
            acct = row['suggested_account']
            for t in tokens:
                index.setdefault(t, set()).add(acct)
        return index

    def suggest(self, text, top_k=3):
        """Return top_k suggestions as list of dicts: {account, confidence, explanation}.

        Confidence is heuristic: exact match -> 1.0, token-match based score otherwise.
        """
        text_norm = text.strip()
        # exact match
        exact = self.df[self.df['extracted_invoice_text'].str.lower() == text_norm.lower()]
        if not exact.empty:
            acct = exact.iloc[0]['suggested_account']
            return [{'account': acct, 'confidence': 1.0, 'explanation': 'Exact match from sample data.'}]

        tokens = self._tokenize(text)
        counter = Counter()
        for t in tokens:
            for acct in self.keyword_index.get(t, []):
                counter[acct] += 1

        if not counter:
            # fallback: return the most frequent account in dataset with low confidence
            most = self.df['suggested_account'].value_counts().idxmax()
            return [{'account': most, 'confidence': 0.15, 'explanation': 'Fallback to most frequent account.'}]

        total = sum(counter.values())
        suggestions = []
        for acct, count in counter.most_common(top_k):
            confidence = round(count / total, 2)
            explanations = f"Matched {count} token(s) from input"
            suggestions.append({'account': acct, 'confidence': confidence, 'explanation': explanations})

        return suggestions

if __name__ == '__main__':
    p = GLPredictor()
    samples = [
        'Transportkosten Lieferung Baustelle Zürich',
        'Bohrmaschine Bosch GSB 13',
        'Unkown item that is new'
    ]
    for s in samples:
        print(s, '->', p.suggest(s))
