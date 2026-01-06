python evaluate_fewshot_v2.py
PS C:\Users\Apoor\ai-account-coding-engine\ai-account-coding-engine> python evaluate_fewshot_v2.py
================================================================================
FEW-SHOT LEARNING WITH FULL TRAINING DATASET
All 39 Training Samples + Token Usage Tracking
================================================================================

📂 Dataset loaded:
   Training samples: 39
   Test samples: 10
   Unique GL accounts: 9

📚 Using ALL 39 training examples for few-shot context
   First 5 examples:
   1. "DeWalt Trennscheibe Stahl Ø125x1mm..." → 6100 – Tools & Equipment
   2. "Transportkosten Lieferung Baustelle Zürich..." → 4900 – Transport & Freight Costs
   3. "Nagel flach 2.5x60mm 2.5kg..." → 4200 – Consumables
   4. "Speditionszuschlag Express..." → 4980 – Surcharges & Fees
   5. "Entsorgungskosten Bauschutt..." → 4200 – Consumables
   ... (+ 34 more examples)


================================================================================
FEW-SHOT EVALUATION: 10 Test Samples
Using 39 training examples as context
================================================================================

[1/10] Werkzeugkoffer leer...
    Expected: 6100 – Tools & Equipment
    AI Top-1: 6100 – Tools & Equipment ✓
    Tokens: 1460 (prompt: 1297, completion: 163)

[2/10] Zollgebühren Import...
    Expected: 4900 – Transport & Freight Costs
    AI Top-1: 4980 – Surcharges & Fees ✗
    Tokens: 1447 (prompt: 1297, completion: 150)

[3/10] LED Baustrahler 50W...
    Expected: 4200 – Consumables
    AI Top-1: 6100 – Tools & Equipment ✗
    Tokens: 1447 (prompt: 1299, completion: 148)

[4/10] Energiezuschlag...
    Expected: 4980 – Surcharges & Fees
    AI Top-1: 4980 – Surcharges & Fees ✓
    Tokens: 1437 (prompt: 1297, completion: 140)

[5/10] Hydraulikschlauch DN12...
    Expected: 4200 – Consumables
    AI Top-1: 3000 – Raw Materials ✗
    Tokens: 1440 (prompt: 1300, completion: 140)

[6/10] Beratungsleistung Engineering...
    Expected: 6000 – External Services
    AI Top-1: 6000 – External Services ✓
    Tokens: 1434 (prompt: 1297, completion: 137)

[7/10] Reparaturkosten Maschine Linie A...
    Expected: 6000 – External Services
    AI Top-1: 6000 – External Services ✓
    Tokens: 1440 (prompt: 1299, completion: 141)

[8/10] Isolationsmaterial Mineralwolle...
    Expected: 4200 – Consumables
    AI Top-1: 4200 – Consumables ✓
    Tokens: 1440 (prompt: 1299, completion: 141)

[9/10] Kleinmengenzuschlag...
    Expected: 4980 – Surcharges & Fees
    AI Top-1: 4980 – Surcharges & Fees ✓
    Tokens: 1445 (prompt: 1298, completion: 147)

[10/10] Elektrokabel NYM-J 3x1.5...
    Expected: 3000 – Raw Materials
    AI Top-1: 3000 – Raw Materials ✓
    Tokens: 1447 (prompt: 1305, completion: 142)


FEW-SHOT RESULTS: 7/10 correct (Accuracy: 70.0%)

📊 TOKEN USAGE SUMMARY:
   Total prompt tokens:     12,988
   Total completion tokens: 1,449
   Total tokens:            14,437
   Average per request:     1444 tokens


================================================================================
RESULTS SUMMARY
================================================================================
Few-Shot Accuracy: 70.0% (7/10)
Training Examples Used: 39
Average Tokens/Request: 1444
Total Tokens: 14,437

✅ Results saved:
   - evaluation_fewshot.csv
   - evaluation_fewshot_summary.json

================================================================================
AI TRAINING OPTIONS EXPLAINED
================================================================================

1. FEW-SHOT LEARNING (Current Approach)
   - Include training examples in every API request
   - Pros: No special setup, flexible, immediate
   - Cons: High token usage (every request includes all examples)
   - Best for: Small datasets (<50 examples), rapid prototyping
   - Cost: ~1,443 tokens/request = $1.44/1k requests @ $0.001/1k tokens

2. FINE-TUNING
   - Train a custom model on your data
   - Pros: Lower inference cost, faster responses, better performance
   - Cons: Requires setup, minimum 10-50 examples, $$ training cost
   - Best for: >100 labeled examples, production use
   - Cost: $8/1M tokens training + $3/1M tokens inference

3. RAG (Retrieval-Augmented Generation)
   - Store examples in vector database, retrieve relevant ones per request
   - Pros: Scalable, only includes relevant examples, updatable
   - Cons: Requires vector DB (Pinecone/Weaviate), embedding costs
   - Best for: Large knowledge bases, frequent updates
   - Cost: Embedding + storage + retrieval (~$0.0001/request)

4. EMBEDDINGS + SEMANTIC SEARCH
   - Pre-compute embeddings for all accounts, find closest match
   - Pros: Very fast, cheap, interpretable
   - Cons: No reasoning, requires good account descriptions
   - Best for: Simple classification, low-cost production
   - Cost: One-time embedding ($0.0001/1k tokens) + search (free)

RECOMMENDATION FOR YOUR PROJECT:
- Current stage: Continue with few-shot (39 examples = manageable token cost)
- When you have 100+ examples: Implement RAG with vector search
- When you have 500+ examples: Consider fine-tuning for production
- Always keep rule-based as primary (it's free and deterministic!)

