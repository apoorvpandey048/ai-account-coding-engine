"""Main account coding engine orchestrating classification and mapping."""

from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging

from .classifier import SemanticClassifier
from .mapper import AccountMapper

logger = logging.getLogger(__name__)


class AccountCodingEngine:
    """Main engine for AI-based account coding of invoice line items."""
    
    def __init__(
        self,
        azure_openai_client: Optional[AzureOpenAI] = None,
        chart_of_accounts: Optional[Dict[str, List[str]]] = None
    ):
        """Initialize the account coding engine.
        
        Args:
            azure_openai_client: Azure OpenAI client for LLM-based classification
            chart_of_accounts: Custom chart of accounts mapping
        """
        self.classifier = SemanticClassifier(azure_client=azure_openai_client)
        self.mapper = AccountMapper(chart_of_accounts=chart_of_accounts)
        logger.info("AccountCodingEngine initialized successfully")
    
    def suggest_accounts(
        self,
        invoice_text: str,
        supplier: Optional[str] = None,
        quantity: Optional[float] = None,
        unit_of_measure: Optional[str] = None,
        unit_price: Optional[float] = None,
        line_amount: Optional[float] = None,
        product_group: Optional[str] = None,
        po_reference: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, any]:
        """Generate GL account coding suggestions for an invoice line item.
        
        Args:
            invoice_text: Invoice line item description (required)
            supplier: Supplier name or ID
            quantity: Line item quantity
            unit_of_measure: Unit of measure (e.g., kg, pcs, m)
            unit_price: Price per unit
            line_amount: Total line amount
            product_group: Product group classification
            po_reference: Purchase order reference
            top_k: Number of suggestions to return (default: 3)
            
        Returns:
            Dictionary containing:
                - suggestions: List of GL account suggestions with confidence and explanation
                - semantic_category: Classified semantic category
                - classification_confidence: Confidence of classification
                - classification_method: Method used (rule/llm/hybrid)
                - metadata: Input metadata for reference
        """
        logger.info(f"Processing suggestion request for: '{invoice_text[:50]}...'")
        
        # Step 1: Classify the invoice text
        classification = self.classifier.classify(
            invoice_text=invoice_text,
            supplier=supplier,
            product_group=product_group
        )
        
        logger.info(
            f"Classification: {classification['category']} "
            f"(confidence: {classification['confidence']:.2f}, "
            f"method: {classification['method']})"
        )
        
        # Step 2: Map category to GL accounts
        suggestions = self.mapper.map_to_accounts(
            category=classification["category"],
            classification_confidence=classification["confidence"],
            invoice_text=invoice_text,
            supplier=supplier,
            top_k=top_k
        )
        
        logger.info(f"Generated {len(suggestions)} account suggestions")
        
        # Step 3: Build response
        response = {
            "suggestions": suggestions,
            "semantic_category": classification["category"],
            "classification_confidence": round(classification["confidence"], 3),
            "classification_method": classification["method"],
            "classification_reasoning": classification["reasoning"],
            "metadata": {
                "invoice_text": invoice_text,
                "supplier": supplier,
                "quantity": quantity,
                "unit_of_measure": unit_of_measure,
                "unit_price": unit_price,
                "line_amount": line_amount,
                "product_group": product_group,
                "po_reference": po_reference
            }
        }
        
        return response
    
    def batch_suggest(
        self,
        line_items: List[Dict[str, any]],
        top_k: int = 3
    ) -> List[Dict[str, any]]:
        """Process multiple invoice line items in batch.
        
        Args:
            line_items: List of line items, each with invoice_text and optional fields
            top_k: Number of suggestions per item
            
        Returns:
            List of suggestion results, one per line item
        """
        logger.info(f"Processing batch of {len(line_items)} line items")
        
        results = []
        for idx, item in enumerate(line_items):
            try:
                result = self.suggest_accounts(
                    invoice_text=item.get("invoice_text", ""),
                    supplier=item.get("supplier"),
                    quantity=item.get("quantity"),
                    unit_of_measure=item.get("unit_of_measure"),
                    unit_price=item.get("unit_price"),
                    line_amount=item.get("line_amount"),
                    product_group=item.get("product_group"),
                    po_reference=item.get("po_reference"),
                    top_k=top_k
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing line item {idx}: {e}")
                results.append({
                    "error": str(e),
                    "line_item_index": idx
                })
        
        logger.info(f"Batch processing complete: {len(results)} results")
        return results
    
    def update_chart_of_accounts(
        self,
        chart_of_accounts: Dict[str, List[str]]
    ) -> None:
        """Update the chart of accounts mapping.
        
        Args:
            chart_of_accounts: New mapping of categories to GL accounts
        """
        self.mapper = AccountMapper(chart_of_accounts=chart_of_accounts)
        logger.info("Chart of accounts updated")
