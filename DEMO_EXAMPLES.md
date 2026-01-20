# AI Account Coding - Demo Results Examples

Generated from `demo_results.json` — processing all 88 invoice items with Pos-based prioritization.

---

## First Example

**Item:** Streng duct PP-HM Sickerrohr SN4 Ø150mm L5m  
**Invoice:** 1_Invoice_fields.json, Item #1, Pos 10  
**Amount:** CHF 224.00 (20 M @ CHF 11.20)

### Results
- **Category:** Material  
- **Method:** Hybrid (rule + LLM agreement)  
- **Confidence:** 98%  
- **Reasoning:** "Rule and LLM agree: The item is a PP-HM drainage pipe, which is a raw material used in construction similar to the example 'Kupferrohr 15mm'."

### Top 3 Suggestions
1. **1220 – Materialvorräte** — 100.0% confidence  
   *Primary account for category 'Material' (Pos signal: prioritized for Pos 10)*

2. **1270 – Angefangene Arbeiten** — 68.9% confidence  
   *Alternative account for category 'Material' (Pos signal: prioritized for Pos 10)*

3. **1200 – Waren** — 54.2% confidence  
   *Alternative account for category 'Material' (Pos signal: prioritized for Pos 10)*

---

## Classification Method Variety

### 1. Hybrid Method (22 examples, 25%)
**When:** Rule-based patterns + LLM agree on classification

**Example:** Same as first example above  
*PP-HM drainage pipe classified as Material with 98% confidence*

---

### 2. LLM Method (47 examples, 53.4%)
**When:** LLM classification used (most complex items)

**Item:** Streng duct PP-HM Abzweiger 45° SN8 (SN12) Ø160/110mm  
**Pos:** 40 | **Amount:** CHF 84.00

**Results:**
- **Category:** Material  
- **Method:** LLM  
- **Confidence:** 95%  
- **Top Suggestion:** 1220 – Materialvorräte (100.0%)

---

### 3. Rule Method (10 examples, 11.4%)
**When:** Strong keyword match in rule-based patterns

**Item:** Rapido Drahtbinder geschweisst 10cm 1000St. (20 Bd/Sack)  
**Pos:** 10 | **Amount:** CHF 1'176.00

**Results:**
- **Category:** Consumables  
- **Method:** Rule  
- **Confidence:** 95%  
- **Reasoning:** "Matched keyword patterns: ['draht', 'binder'] → Consumables"  
- **Top Suggestion:** 1220 – Materialvorräte (100.0%)

---

### 4. Hybrid-LLM Method (7 examples, 8%)
**When:** Rule suggests one category, LLM suggests another (LLM wins)

**Item:** PP Schachtfutter Grip Ø160mm inkl. Dichtung  
**Pos:** 70 | **Amount:** CHF 28.00

**Results:**
- **Category:** Material  
- **Method:** Hybrid-LLM  
- **Confidence:** 88%  
- **Top Suggestion:** 1220 – Materialvorräte (94.2%)

---

### 5. Hybrid-Rule Method (2 examples, 2.3%)
**When:** Rule suggests one category, LLM suggests another (Rule wins due to stronger confidence)

**Item:** Streng duct PP-HM Bogen 45° SN8 (SN12) Ø160mm  
**Pos:** 50 | **Amount:** CHF 51.00

**Results:**
- **Category:** Safety  
- **Method:** Hybrid-Rule  
- **Confidence:** 70%  
- **Top Suggestion:** 1220 – Materialvorräte (73.5%)

---

## Key Features Demonstrated

✅ **Pos-based prioritization** — All 3 suggestions show "Pos signal: prioritized for Pos X" when applicable  
✅ **Multi-method classification** — Hybrid intelligence combining rules + LLM  
✅ **High confidence** — Average top-suggestion confidence: 94.6%  
✅ **Complete explanations** — Every suggestion includes reasoning  
✅ **Real GL accounts** — From Kontoplan.csv (Swiss chart of accounts)

---

## Summary Statistics

- **Total Items Processed:** 88  
- **Classification Breakdown:**
  - LLM: 47 (53.4%)
  - Hybrid: 22 (25.0%)
  - Rule: 10 (11.4%)
  - Hybrid-LLM: 7 (8.0%)
  - Hybrid-Rule: 2 (2.3%)
- **Success Rate:** 100% (all items classified)
- **Average Suggestions per Item:** 3
