import pandas as pd
import re
from collections import Counter
from fuzzywuzzy import fuzz
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Download required NLTK data (silently if already present)
try:
    nltk.data.find('corpora/wordnet')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Embeddings imports (optional)
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

class GLPredictor:
    """Enhanced rule-based GL predictor with multiple matching strategies.
    
    Uses fuzzy matching, lemmatization, synonyms, and optional semantic embeddings
    to improve accuracy on unseen data.
    """

    def __init__(self, mapping_csv=None):
        if mapping_csv is None:
            # Use training split for rule-based model
            mapping_csv = 'data/train_split.csv'
        self.df = pd.read_csv(mapping_csv)
        # parse suggested_account into code and label if present
        self.df[['account_code','account_label']] = self.df['suggested_account'].str.split(' – ', n=1, expand=True)
        
        # Initialize text processing
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('german') + stopwords.words('english'))
        
        # Synonym/domain vocabulary expansion for better matching
        self.synonyms = {
            'transport': ['shipping', 'delivery', 'freight', 'logistik', 'lieferung', 'versand', 'zoll', 'customs'],
            'materials': ['rohstoffe', 'raw', 'supplies', 'materialien', 'kabel', 'cable', 'elektro'],
            'tools': ['equipment', 'werkzeug', 'geräte', 'maschine', 'machine', 'werkzeugkoffer', 'toolbox', 'bohrmaschine'],
            'services': ['dienstleistung', 'consulting', 'beratung', 'support', 'reparatur', 'repair', 'engineering', 'reparaturkosten'],
            'fees': ['gebühren', 'surcharges', 'zuschläge', 'charges', 'energiezuschlag', 'kleinmengenzuschlag'],
            'consumables': ['verbrauchsmaterial', 'supplies', 'bürobedarf', 'office', 'led', 'baustrahler', 'hydraulik', 'isolation'],
        }
        
        # Account-specific keyword patterns to improve classification of ambiguous cases
        self.account_patterns = {
            '6100 – Tools & Equipment': ['werkzeugkoffer', 'toolbox', 'bohrmaschine', 'drill', 'säge', 'saw'],
            '6000 – External Services': ['beratung', 'consulting', 'engineering', 'reparatur', 'repair', 'reparaturkosten', 'dienstleistung', 'service'],
            '4900 – Transport & Freight Costs': ['zoll', 'customs', 'zollgebühren', 'freight', 'fracht', 'transport'],
            '4980 – Surcharges & Fees': ['zuschlag', 'surcharge', 'energiezuschlag', 'kleinmengenzuschlag', 'gebühr', 'fee'],
            '3000 – Raw Materials': ['kabel', 'cable', 'elektrokabel', 'draht', 'wire', 'rohstoff'],
        }
        
        # Initialize embeddings model for semantic search (lightweight multilingual model)
        self.use_embeddings = False
        if EMBEDDINGS_AVAILABLE:
            try:
                print("Loading embeddings model (first run may take a moment)...")
                self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                # Pre-compute embeddings for all training texts
                self.training_texts = self.df['extracted_invoice_text'].tolist()
                self.training_embeddings = self.embedding_model.encode(self.training_texts, convert_to_numpy=True)
                self.use_embeddings = True
                print(f"✓ Embeddings initialized for {len(self.training_texts)} training examples")
            except Exception as e:
                print(f"Warning: Could not load embeddings model: {e}")
                self.use_embeddings = False
        
        # build keyword index from invoice texts
        self.keyword_index = self._build_keyword_index()

    def _tokenize(self, text):
        """Enhanced tokenization with lemmatization and stopword removal."""
        text = text.lower()
        # Extract alphanumeric tokens including German characters
        tokens = re.findall(r"[a-z0-9äöüß]+", text)
        
        # Lemmatize and filter stopwords
        processed = []
        for token in tokens:
            if len(token) > 2 and token not in self.stop_words:
                try:
                    lemma = self.lemmatizer.lemmatize(token)
                    processed.append(lemma)
                except:
                    processed.append(token)
        
        # Add synonym expansions
        expanded = set(processed)
        for token in processed:
            for key, syns in self.synonyms.items():
                if token in syns or token == key:
                    expanded.update(syns)
                    expanded.add(key)
        
        return list(expanded)

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

        Uses multiple strategies (in order of priority):
        1. Exact match (confidence 1.0)
        1.5. Account-specific pattern match (confidence 0.85)
        2. Semantic similarity via embeddings (confidence 0.6-0.95)
        3. Fuzzy string matching (confidence 0.5-0.85)
        4. Enhanced token matching with synonyms (confidence 0.3-0.7)
        5. Fallback to most frequent (confidence 0.15)
        """
        text_norm = text.strip()
        text_lower = text_norm.lower()
        
        # Strategy 1: Exact match
        exact = self.df[self.df['extracted_invoice_text'].str.lower() == text_lower]
        if not exact.empty:
            acct = exact.iloc[0]['suggested_account']
            return [{'account': acct, 'confidence': 1.0, 'explanation': 'Exact match from training data.'}]

        # Strategy 1.5: Check account-specific patterns for high-confidence keyword matches
        for account, patterns in self.account_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return [{'account': account, 'confidence': 0.85, 'explanation': f'Matched account pattern: "{pattern}"'}]

        # Strategy 2: Semantic similarity using embeddings
        if self.use_embeddings:
            try:
                query_embedding = self.embedding_model.encode([text_norm], convert_to_numpy=True)
                similarities = cosine_similarity(query_embedding, self.training_embeddings)[0]
                
                # Get top matches above threshold
                top_indices = np.argsort(similarities)[::-1][:top_k]
                best_similarity = float(similarities[top_indices[0]])  # Convert numpy float to Python float
                
                if best_similarity >= 0.65:  # High semantic similarity threshold
                    suggestions = []
                    for idx in top_indices:
                        sim_score = float(similarities[idx])  # Convert numpy float to Python float
                        if sim_score >= 0.5:  # Minimum threshold
                            acct = self.df.iloc[idx]['suggested_account']
                            # Map similarity to confidence: 0.65->0.6, 1.0->0.95
                            confidence = 0.5 + (sim_score - 0.5) * 0.9
                            explanation = f"Semantic similarity: {sim_score:.2f}"
                            suggestions.append({'account': acct, 'confidence': round(float(confidence), 2), 'explanation': explanation})
                    
                    if suggestions:
                        return suggestions[:top_k]
            except Exception as e:
                print(f"Embeddings error: {e}")

        # Strategy 3: Fuzzy string matching against all training examples
        best_fuzzy_match = None
        best_fuzzy_score = 0
        for _, row in self.df.iterrows():
            score = fuzz.token_set_ratio(text_norm.lower(), row['extracted_invoice_text'].lower())
            if score > best_fuzzy_score:
                best_fuzzy_score = score
                best_fuzzy_match = row['suggested_account']
        
        if best_fuzzy_score >= 80:  # High fuzzy match threshold
            confidence = 0.5 + (best_fuzzy_score - 80) * 0.015  # 0.50 to 0.80
            return [{'account': best_fuzzy_match, 'confidence': round(confidence, 2), 
                    'explanation': f'Fuzzy text match (similarity: {best_fuzzy_score}%)'}]

        # Strategy 4: Enhanced token matching with synonyms
        tokens = self._tokenize(text)
        counter = Counter()
        for t in tokens:
            for acct in self.keyword_index.get(t, []):
                counter[acct] += 1

        if counter:
            total = sum(counter.values())
            suggestions = []
            for acct, count in counter.most_common(top_k):
                # Boost confidence for multi-token matches
                base_confidence = count / total
                boosted = min(0.7, base_confidence * 1.5)  # Cap at 0.7 for token-based
                confidence = round(boosted, 2)
                explanations = f"Matched {count} relevant token(s)"
                suggestions.append({'account': acct, 'confidence': confidence, 'explanation': explanations})
            return suggestions

        # Strategy 5: Medium-quality fuzzy match fallback
        if best_fuzzy_score >= 50:
            confidence = 0.2 + (best_fuzzy_score - 50) * 0.01  # 0.20 to 0.50
            return [{'account': best_fuzzy_match, 'confidence': round(confidence, 2), 
                    'explanation': f'Weak fuzzy match (similarity: {best_fuzzy_score}%)'}]

        # Strategy 6: Ultimate fallback
        most = self.df['suggested_account'].value_counts().idxmax()
        return [{'account': most, 'confidence': 0.15, 'explanation': 'Fallback to most frequent account.'}]

if __name__ == '__main__':
    p = GLPredictor()
    samples = [
        'Transportkosten Lieferung Baustelle Zürich',
        'Bohrmaschine Bosch GSB 13',
        'Unkown item that is new'
    ]
    for s in samples:
        print(s, '->', p.suggest(s))
