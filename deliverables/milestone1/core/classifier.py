"""Semantic classification of invoice line items using rule-based and LLM logic."""

import re
from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging

logger = logging.getLogger(__name__)


class SemanticClassifier:
    """Classifies invoice line items into semantic categories."""
    
    # Rule-based keywords for common categories
    CATEGORY_KEYWORDS = {
        "Material": [
            r"rohr", r"edelstahl", r"kupfer", r"aluminium", r"holz", r"metall",
            r"stahl", r"blech", r"profil", r"material", r"rohstoff"
        ],
        "Consumables": [
            r"schraube", r"nagel", r"dichtung", r"klebe", r"band", r"draht",
            r"scheibe", r"verpackung", r"kartusche", r"verbrauch", r"kleinteile"
        ],
        "Transport": [
            r"transport", r"fracht", r"lieferung", r"versand", r"spedition",
            r"logistik", r"zustellung", r"expresszuschlag"
        ],
        "Surcharge": [
            r"zuschlag", r"gebühr", r"pauschale", r"zoll", r"bearbeitungs",
            r"kleinmengen", r"energie", r"pfand"
        ],
        "IT & Software": [
            r"software", r"lizenz", r"licence", r"license", r"cad", r"it support", r"server",
            r"digital", r"cloud", r"saas", r"itunes", r"adobe"
        ],
        "Tools": [
            r"werkzeug", r"bohr", r"schleif", r"säge", r"trennscheibe",
            r"maschine", r"gerät", r"dewalt", r"bosch"
        ],
        "Service": [
            r"service", r"wartung", r"reparatur", r"montage", r"beratung",
            r"projektmanagement", r"engineering", r"dienstleistung"
        ],
        "Safety": [
            r"schutz", r"helm", r"brille", r"handschuh", r"sicherheit",
            r"ppe", r"arbeitsschutz"
        ],
        "Operating Supplies": [
            r"öl", r"schmierstoff", r"kühlflüssigkeit", r"reinigung",
            r"betriebsstoff", r"hilfsstoff"
        ]
    }
    
    def __init__(self, azure_client: Optional[AzureOpenAI] = None):
        """Initialize classifier with optional Azure OpenAI client.
        
        Args:
            azure_client: Azure OpenAI client for LLM-based classification
        """
        self.azure_client = azure_client
    
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
    
    def _rule_based_classify(self, invoice_text: str) -> Dict[str, any]:
        """Classify using keyword matching rules.
        
        Args:
            invoice_text: The invoice line item text
            
        Returns:
            Classification result with category, confidence, method, reasoning
        """
        text_lower = invoice_text.lower()
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

        # Edge-case overrides: prefer Consumables for screws even when material keywords present
        if "consumables" in (c.lower() for c in matches.keys()) and "material" in (c.lower() for c in matches.keys()):
            if re.search(r"schraub", text_lower, re.IGNORECASE):
                best_category = "Consumables"
                match_count = matches.get(best_category, match_count)

        # Prefer Operating Supplies when 'öl' appears, even if 'maschine' also matches (e.g., 'Maschinenöl')
        if "operating supplies" in (c.lower() for c in matches.keys()) and "tools" in (c.lower() for c in matches.keys()):
            if re.search(r"\böl\b|maschinenöl|schmier", text_lower, re.IGNORECASE):
                best_category = "Operating Supplies"
                match_count = matches.get(best_category, match_count)
        
        # Calculate confidence based on match count and uniqueness
        confidence = min(0.5 + (match_count * 0.15), 0.95)
        if len(matches) > 1:
            # Reduce confidence if multiple categories matched
            confidence *= 0.8
        
        return {
            "category": best_category,
            "confidence": confidence,
            "method": "rule",
            "reasoning": f"Matched {match_count} keyword(s) for {best_category}"
        }
    
    def _llm_classify(
        self,
        invoice_text: str,
        supplier: Optional[str],
        product_group: Optional[str]
    ) -> Dict[str, any]:
        """Classify using Azure OpenAI LLM.
        
        Args:
            invoice_text: The invoice line item text
            supplier: Optional supplier name
            product_group: Optional product group
            
        Returns:
            Classification result with category, confidence, method, reasoning
        """
        categories = list(self.CATEGORY_KEYWORDS.keys())
        
        prompt = f"""You are an expert accountant specialized in classifying invoice line items.

Classify the following invoice line item into ONE of these categories:
{', '.join(categories)}

Invoice line: {invoice_text}
{f'Supplier: {supplier}' if supplier else ''}
{f'Product group: {product_group}' if product_group else ''}

Respond ONLY with valid JSON in this exact format (no additional text):
{{
  "category": "<one of the listed categories>",
  "confidence": <float between 0 and 1>,
  "reasoning": "<brief explanation>"
}}"""
        
        try:
            response = self.azure_client.chat.completions.create(
                model="gpt-4",  # Will be configured via deployment name
                messages=[
                    {"role": "system", "content": "You are a precise accounting classifier. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            # Validate category
            if result.get("category") not in categories:
                result["category"] = "Other"
            
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
        
        # If they disagree, trust LLM more but reduce confidence
        if llm_result["confidence"] > rule_result["confidence"]:
            return {
                "category": llm_result["category"],
                "confidence": llm_result["confidence"] * 0.85,
                "method": "hybrid_llm",
                "reasoning": f"LLM override: {llm_result['reasoning']}"
            }
        
        return {
            "category": rule_result["category"],
            "confidence": rule_result["confidence"] * 0.85,
            "method": "hybrid_rule",
            "reasoning": f"Rule preferred: {rule_result['reasoning']}"
        }
