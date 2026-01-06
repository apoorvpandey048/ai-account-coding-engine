"""Maps semantic categories to GL accounts based on chart of accounts."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AccountMapper:
    """Maps semantic categories to General Ledger account codes."""
    
    # Default category to GL account mapping
    DEFAULT_CATEGORY_MAPPING = {
        "Material": ["3000 – Raw Materials"],
        "Consumables": ["4200 – Consumables"],
        "Transport": ["4900 – Transport & Freight Costs"],
        "Surcharge": ["4980 – Surcharges & Fees"],
        "IT & Software": ["6500 – IT & Software Expenses"],
        "Tools": ["6100 – Tools & Equipment"],
        "Service": ["6000 – External Services"],
        "Safety": ["6250 – Safety Equipment (PPE)"],
        "Operating Supplies": ["4300 – Operating Supplies"],
        "Other": ["4200 – Consumables"]  # Default fallback
    }
    
    def __init__(self, chart_of_accounts: Optional[Dict[str, List[str]]] = None):
        """Initialize mapper with custom or default chart of accounts.
        
        Args:
            chart_of_accounts: Custom mapping of categories to GL accounts.
                             If None, uses DEFAULT_CATEGORY_MAPPING.
        """
        self.chart_of_accounts = chart_of_accounts or self.DEFAULT_CATEGORY_MAPPING
        logger.info(f"Initialized AccountMapper with {len(self.chart_of_accounts)} categories")
    
    def map_to_accounts(
        self,
        category: str,
        classification_confidence: float,
        invoice_text: str,
        supplier: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, any]]:
        """Map a semantic category to GL account suggestions.
        
        Args:
            category: Semantic category from classifier
            classification_confidence: Confidence score from classification
            invoice_text: Original invoice line item text
            supplier: Optional supplier name for context
            top_k: Number of top suggestions to return (default: 3)
            
        Returns:
            List of account suggestions, each containing:
                - account: GL account code and name
                - confidence: Confidence score for this suggestion
                - explanation: Why this account was suggested
        """
        # Get potential accounts for this category
        potential_accounts = self.chart_of_accounts.get(
            category,
            self.chart_of_accounts.get("Other", ["4200 – Consumables"])
        )
        
        suggestions = []
        
        for idx, account in enumerate(potential_accounts[:top_k]):
            # Calculate suggestion confidence
            # Primary account gets full classification confidence
            # Alternative accounts get reduced confidence
            if idx == 0:
                account_confidence = classification_confidence
                explanation = f"Primary account for category '{category}'"
            else:
                account_confidence = classification_confidence * (0.7 - idx * 0.15)
                explanation = f"Alternative account for category '{category}'"
            
            # Add context to explanation
            if supplier:
                explanation += f" (Supplier: {supplier})"
            
            suggestions.append({
                "account": account,
                "confidence": round(account_confidence, 3),
                "explanation": explanation
            })
        
        # If we don't have enough suggestions, add fallback
        if len(suggestions) < top_k and category != "Other":
            fallback_accounts = self.chart_of_accounts.get("Other", [])
            for account in fallback_accounts:
                if len(suggestions) >= top_k:
                    break
                if account not in [s["account"] for s in suggestions]:
                    suggestions.append({
                        "account": account,
                        "confidence": round(classification_confidence * 0.3, 3),
                        "explanation": "Fallback account for uncertain classification"
                    })
        
        # Sort by confidence descending
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return suggestions[:top_k]
    
    def update_mapping(self, category: str, accounts: List[str]) -> None:
        """Update the chart of accounts mapping for a category.
        
        Args:
            category: Semantic category to update
            accounts: List of GL account codes to map to this category
        """
        self.chart_of_accounts[category] = accounts
        logger.info(f"Updated mapping for category '{category}' with {len(accounts)} accounts")
    
    def get_all_accounts(self) -> List[str]:
        """Get all GL accounts across all categories.
        
        Returns:
            Flat list of all unique GL account codes
        """
        all_accounts = set()
        for accounts in self.chart_of_accounts.values():
            all_accounts.update(accounts)
        return sorted(list(all_accounts))
    
    def validate_account(self, account: str) -> bool:
        """Check if an account exists in the chart of accounts.
        
        Args:
            account: GL account code to validate
            
        Returns:
            True if account exists, False otherwise
        """
        all_accounts = self.get_all_accounts()
        return account in all_accounts
