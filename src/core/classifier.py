"""Semantic classification of invoice line items using rule-based and LLM logic."""

import re
import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging
import random

logger = logging.getLogger(__name__)


class SemanticClassifier:
    """Classifies invoice line items into semantic categories."""
    
    # Rule-based keywords for common categories (enhanced with training data patterns)
    CATEGORY_KEYWORDS = {
        "Material": [
            r"rohr", r"edelstahl", r"kupfer", r"aluminium", r"holz", r"metall",
            r"stahl", r"blech", r"profil", r"material", r"rohstoff",
            r"kabel", r"elektrokabel", r"nym", r"holzlatte", r"spanplatte",
            r"mineralwolle", r"isolation"
        ],
        "Consumables": [
            r"schraube", r"nagel", r"dichtung", r"klebe", r"band", r"draht",
            r"scheibe", r"verpackung", r"kartusche", r"verbrauch", r"kleinteile",
            r"led\s+(bau)?strahler", r"baustrahler", r"weichschaumstoff",
            r"schlauch", r"hydraulik", r"bauchemie", r"dichtungsband",
            r"verbrauchsmaterial", r"rapido", r"drahtbinder"
        ],
        "Transport": [
            r"transport", r"fracht", r"lieferung", r"versand", r"spedition",
            r"logistik", r"zustellung", r"expresszuschlag", r"baustelle",
            r"inland", r"ausland", r"zoll"
        ],
        "Surcharge": [
            r"zuschlag", r"gebühr", r"pauschale", r"bearbeitungs",
            r"kleinmengen", r"energie", r"pfand", r"paletten"
        ],
        "IT & Software": [
            r"software", r"lizenz", r"cad", r"it\s+support", r"server",
            r"digital", r"cloud", r"saas"
        ],
        "Tools": [
            r"werkzeug", r"bohr", r"schleif", r"säge", r"trennscheibe",
            r"maschine", r"gerät", r"dewalt", r"bosch", r"koffer"
        ],
        "Service": [
            r"service", r"wartung", r"reparatur", r"montage", r"beratung",
            r"projektmanagement", r"engineering", r"dienstleistung",
            r"reparaturkosten", r"linie\s+[a-z]"
        ],
        "Safety": [
            r"schutz", r"helm", r"brille", r"handschuh", r"sicherheit",
            r"ppe", r"arbeitsschutz", r"nitril", r"en\s*\d+"
        ],
        "Operating Supplies": [
            r"öl", r"maschinenöl", r"schmierstoff", r"schmierfett",
            r"kühlflüssigkeit", r"reinigung", r"betriebsstoff", r"hilfsstoff"
        ]
    }
    
    def __init__(self, azure_client: Optional[AzureOpenAI] = None):
        """Initialize classifier with optional Azure OpenAI client.
        
        Args:
            azure_client: Azure OpenAI client for LLM-based classification
        """
        self.azure_client = azure_client
        self.training_examples = self._load_training_examples()
    
    def _load_training_examples(self) -> List[Dict[str, str]]:
        """Load training examples from invoice_text_with_accounts.csv.
        
        Returns:
            List of training examples with text and account
        """
        try:
            base_dir = Path(__file__).parent.parent.parent
            examples = []

            # Primary: load from provided JSON examples (3_examples/all_Invoice_fields.json)
            json_path = base_dir / "3_examples" / "all_Invoice_fields.json"
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    for _, doc in data.items():
                        fields = doc.get("Fields", {})
                        artikel = fields.get("Artikel", [])
                        for item in artikel:
                            text = item.get("Bezeichnung") or item.get("Beschreibung") or item.get("Art-Nr") or ""
                            if not text:
                                continue
                            examples.append({"text": text, "account": ""})
                    logger.info(f"Loaded {len(examples)} training examples from {json_path.name}")
                    return examples
                except Exception as e:
                    logger.warning(f"Failed to parse {json_path}: {e}")

            # Fallback: if a CSV of invoice examples exists in data, try to read it without requiring pandas
            # Also allow Kontoplan.csv (approved by user) to provide account descriptions
            kontoplan_path = base_dir / "data" / "Kontoplan.csv"
            if kontoplan_path.exists():
                try:
                    with open(kontoplan_path, encoding='utf-8') as kf:
                        for line in kf:
                            line = line.strip()
                            if not line:
                                continue
                            # Expect format: code;'Description'
                            parts = line.split(";")
                            if len(parts) >= 2:
                                code = parts[0].strip().strip("'")
                                desc = parts[1].strip().strip("'")
                                if desc:
                                    examples.append({"text": desc, "account": f"{code} – {desc}"})
                    logger.info(f"Loaded {len(examples)} Kontoplan entries from {kontoplan_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to read Kontoplan {kontoplan_path}: {e}")

            csv_path = base_dir / "data" / "invoice_text_with_accounts.csv"
            if csv_path.exists():
                try:
                    with open(csv_path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            text = row.get("extracted_invoice_text") or row.get("text") or ""
                            account = row.get("suggested_account") or row.get("account") or ""
                            if text:
                                examples.append({"text": text, "account": account})
                    logger.info(f"Loaded {len(examples)} training examples from {csv_path.name}")
                    return examples
                except Exception as e:
                    logger.warning(f"Failed to read CSV fallback {csv_path}: {e}")

            # No allowed training data found — return empty list (rule-based will still operate)
            logger.warning("No training examples found in allowed files; proceeding with empty examples.")
            return []
        except Exception as e:
            logger.error(f"Failed to load training examples: {e}")
            return []
    
    def classify(
        self,
        invoice_text: str,
        supplier: Optional[str] = None,
        product_group: Optional[str] = None
    ) -> Dict[str, any]:
        """Classify an invoice line item into a semantic category.
        
        Args:
            invoice_text: The invoice line item text
            supplier: Optional supplier name
            product_group: Optional product group
            
        Returns:
            Dictionary with:
                - category: The semantic category
                - confidence: Confidence score (0-1)
                - method: Classification method used (rule/llm/hybrid)
                - reasoning: Explanation of classification
        """
        # Try rule-based classification first
        rule_result = self._rule_based_classify(invoice_text)
        
        if rule_result["confidence"] >= 0.8:
            logger.info(f"High-confidence rule-based classification: {rule_result['category']}")
            return rule_result
        
        # For ambiguous cases, use LLM if available
        if self.azure_client:
            llm_result = self._llm_classify(invoice_text, supplier, product_group)
            
            # Combine rule and LLM results for hybrid approach
            if rule_result["confidence"] > 0.3:
                return self._combine_results(rule_result, llm_result)
            
            return llm_result
        
        # Fallback to rule-based result
        logger.warning("No LLM available, using rule-based classification only")
        return rule_result
    
    def _get_few_shot_examples(self, invoice_text: str, num_examples: int = 12) -> str:
        """Select diverse few-shot examples from training data.
        
        Args:
            invoice_text: Current text to classify
            num_examples: Number of examples to include
            
        Returns:
            Formatted string with examples
        """
        if not self.training_examples:
            return "(No training examples available)"
        
        # Get diverse examples by account type
        account_groups = {}
        for ex in self.training_examples:
            account = ex["account"]
            if account not in account_groups:
                account_groups[account] = []
            account_groups[account].append(ex)
        
        # Select 1-2 examples per unique account type
        selected = []
        for account, examples in account_groups.items():
            # Pick one random example from this account
            selected.append(random.choice(examples))
            if len(selected) >= num_examples:
                break
        
        # Shuffle for variety
        random.shuffle(selected)
        
        # Format examples
        examples_list = []
        for i, ex in enumerate(selected[:num_examples], 1):
            # Extract category from account name
            account_parts = ex["account"].split("–")
            category_hint = account_parts[1].strip() if len(account_parts) > 1 else "Other"
            examples_list.append(f"{i}. \"{ex['text']}\" → {ex['account']}")
        
        return "\n".join(examples_list)
    
    def _rule_based_classify(self, invoice_text: str) -> Dict[str, any]:
        """Classify using keyword matching rules.
        
        Args:
            invoice_text: The invoice line item text
            
        Returns:
            Classification result with category, confidence, method, reasoning
        """
        text_lower = invoice_text.lower()
        
        # Check for high-confidence direct patterns first
        direct_match = self._check_direct_patterns(text_lower)
        if direct_match:
            return direct_match
        
        matches = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            match_count = sum(
                1 for pattern in keywords 
                if re.search(pattern, text_lower, re.IGNORECASE)
            )
            if match_count > 0:
                matches[category] = match_count
        
        if not matches:
            return {
                "category": "Other",
                "confidence": 0.1,
                "method": "rule",
                "reasoning": "No keyword matches found"
            }
        
        # Select category with most matches
        best_category = max(matches, key=matches.get)
        match_count = matches[best_category]
        
        # Calculate confidence based on match count and uniqueness
        confidence = min(0.5 + (match_count * 0.15), 0.95)
        if len(matches) > 1:
            # Reduce confidence if multiple categories matched
            confidence *= 0.85
        
        return {
            "category": best_category,
            "confidence": confidence,
            "method": "rule",
            "reasoning": f"Matched {match_count} keyword(s) for {best_category}"
        }
    
    def _check_direct_patterns(self, text_lower: str) -> Optional[Dict[str, any]]:
        """Check for high-confidence direct pattern matches.
        
        Args:
            text_lower: Lowercased invoice text
            
        Returns:
            Classification result if direct match found, None otherwise
        """
        # Direct patterns with very high confidence
        direct_patterns = [
            (r"elektrokabel|kabel\s+nym", "Material", "electrical cable pattern"),
            (r"led\s+baustrahler|baustrahler", "Consumables", "LED lighting pattern"),
            (r"hydraulikschlauch|hydraulik.*schlauch", "Consumables", "hydraulic hose pattern"),
            (r"isolationsmaterial|mineralwolle", "Consumables", "insulation material pattern"),
            (r"beratungsleistung|engineering", "Service", "consulting service pattern"),
            (r"reparaturkosten|reparatur.*maschine", "Service", "repair service pattern"),
            (r"werkzeugkoffer", "Tools", "tool storage pattern"),
            (r"energiezuschlag|kleinmengenzuschlag", "Surcharge", "surcharge pattern"),
            (r"zollgebühren|zoll.*import", "Transport", "customs/import pattern"),
        ]
        
        for pattern, category, desc in direct_patterns:
            if re.search(pattern, text_lower):
                return {
                    "category": category,
                    "confidence": 0.95,
                    "method": "rule",
                    "reasoning": f"Direct match: {desc}"
                }
        
        return None
    
    def _llm_classify(
        self,
        invoice_text: str,
        supplier: Optional[str],
        product_group: Optional[str]
    ) -> Dict[str, any]:
        """Classify using Azure OpenAI LLM with enhanced prompting and training examples.
        
        Args:
            invoice_text: The invoice line item text
            supplier: Optional supplier name
            product_group: Optional product group
            
        Returns:
            Classification result with category, confidence, method, reasoning
        """
        categories = list(self.CATEGORY_KEYWORDS.keys())
        
        # Select diverse few-shot examples from training data
        examples_text = self._get_few_shot_examples(invoice_text)
        
        prompt = f"""You are an expert German accounting classifier for construction/manufacturing invoice line items.

CATEGORY DEFINITIONS:
• Material: Raw materials, metals, pipes, cables, sheets, lumber used in production or construction
• Consumables: Small parts, screws, tapes, packaging, adhesives, supplies consumed regularly
• Transport: Shipping costs, logistics, freight, delivery charges
• Surcharge: Additional fees, customs duties, small quantity surcharges, energy fees, deposits
• IT & Software: Software licenses, digital tools, cloud services, IT support
• Tools: Power tools, equipment, machines, tool storage used for work (not consumed)
• Service: Professional services like repair, consulting, maintenance, engineering, installation
• Safety: Personal protective equipment (PPE), safety gear, helmets, gloves, goggles
• Operating Supplies: Oils, lubricants, coolants, cleaning supplies, greases for operations

TRAINING EXAMPLES FROM YOUR COMPANY:
{examples_text}

TASK:
Classify this invoice line item into ONE category based on the patterns above.

Invoice line: {invoice_text}
{f'Supplier: {supplier}' if supplier else ''}
{f'Product group: {product_group}' if product_group else ''}

Think step-by-step:
1. What specific item or service is being purchased?
2. Which training examples are most similar to this item?
3. How would this be used in a construction/manufacturing business?
4. Is it consumed, used repeatedly, or a one-time service?
5. Which category from the definitions best matches this usage?

Respond with JSON only:
{{
  "category": "<one of: {', '.join(categories)}>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<explain your classification in one sentence>"
}}"""
        
        try:
            model_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
            response = self.azure_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a precise accounting classifier for German construction/manufacturing invoices. Always respond with valid JSON only. Use the category definitions and examples provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            # Validate category
            if result.get("category") not in categories:
                result["category"] = "Other"
            
            # Calibrate confidence to reduce overconfidence
            # If LLM is very confident (>0.9), reduce slightly
            original_confidence = result.get("confidence", 0.5)
            if original_confidence > 0.9:
                result["confidence"] = 0.85 + (original_confidence - 0.9) * 0.5
            
            result["method"] = "llm"
            return result
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {
                "category": "Other",
                "confidence": 0.2,
                "method": "llm_failed",
                "reasoning": f"LLM classification error: {str(e)}"
            }
    
    def _combine_results(
        self,
        rule_result: Dict[str, any],
        llm_result: Dict[str, any]
    ) -> Dict[str, any]:
        """Combine rule-based and LLM results for hybrid classification.
        
        Args:
            rule_result: Result from rule-based classification
            llm_result: Result from LLM classification
            
        Returns:
            Combined classification result
        """
        # If both agree, increase confidence
        if rule_result["category"] == llm_result["category"]:
            combined_confidence = min(
                (rule_result["confidence"] + llm_result["confidence"]) / 1.5,
                0.98
            )
            return {
                "category": rule_result["category"],
                "confidence": combined_confidence,
                "method": "hybrid",
                "reasoning": f"Rule and LLM agree: {llm_result['reasoning']}"
            }
        
        # If rule has very high confidence (>=0.9), trust it more
        if rule_result["confidence"] >= 0.9:
            return {
                "category": rule_result["category"],
                "confidence": rule_result["confidence"] * 0.95,
                "method": "hybrid_rule",
                "reasoning": f"High-confidence rule: {rule_result['reasoning']}"
            }
        
        # If rule has good confidence (>=0.65) and LLM confidence gap is small (<0.25)
        confidence_gap = llm_result["confidence"] - rule_result["confidence"]
        if rule_result["confidence"] >= 0.65 and confidence_gap < 0.25:
            return {
                "category": rule_result["category"],
                "confidence": rule_result["confidence"] * 0.90,
                "method": "hybrid_rule",
                "reasoning": f"Rule with reasonable confidence: {rule_result['reasoning']}"
            }
        
        # Otherwise, if LLM has higher confidence, use it (with calibration)
        if llm_result["confidence"] > rule_result["confidence"]:
            return {
                "category": llm_result["category"],
                "confidence": llm_result["confidence"] * 0.88,
                "method": "hybrid_llm",
                "reasoning": f"LLM override: {llm_result['reasoning']}"
            }
        
        # Default to rule result
        return {
            "category": rule_result["category"],
            "confidence": rule_result["confidence"] * 0.90,
            "method": "hybrid_rule",
            "reasoning": f"Rule preferred: {rule_result['reasoning']}"
        }
