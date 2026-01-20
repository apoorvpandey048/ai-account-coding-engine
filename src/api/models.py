"""API models and schemas using Pydantic."""

from typing import Optional, List
from pydantic import BaseModel, Field, validator


class LineItemRequest(BaseModel):
    """Request model for a single invoice line item."""
    
    invoice_text: str = Field(..., description="Invoice line item description text", min_length=1)
    supplier: Optional[str] = Field(None, description="Supplier name or ID")
    quantity: Optional[float] = Field(None, description="Line item quantity", gt=0)
    unit_of_measure: Optional[str] = Field(None, description="Unit of measure (e.g., kg, pcs, m)")
    unit_price: Optional[float] = Field(None, description="Price per unit", ge=0)
    line_amount: Optional[float] = Field(None, description="Total line amount", ge=0)
    product_group: Optional[str] = Field(None, description="Product group classification")
    po_reference: Optional[str] = Field(None, description="Purchase order reference")
    pos: Optional[str] = Field(None, description="Invoice line position (Pos) when available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "invoice_text": "Edelstahlrohr 12x1.5 mm",
                "supplier": "MetalWorks GmbH",
                "quantity": 50,
                "unit_of_measure": "pcs",
                "unit_price": 12.50,
                "line_amount": 625.00,
                "product_group": "Metal Pipes",
                    "po_reference": "PO-2026-001",
                    "pos": "10"
            }
        }


class SuggestRequest(BaseModel):
    """Request model for account suggestion endpoint."""
    
    line_item: LineItemRequest = Field(..., description="Invoice line item to classify")
    top_k: int = Field(3, description="Number of account suggestions to return", ge=1, le=5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "line_item": {
                    "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
                    "supplier": "Express Logistics",
                    "line_amount": 150.00
                },
                "top_k": 3
            }
        }


class BatchSuggestRequest(BaseModel):
    """Request model for batch account suggestions."""
    
    line_items: List[LineItemRequest] = Field(..., description="List of invoice line items", min_length=1, max_length=100)
    top_k: int = Field(3, description="Number of account suggestions per item", ge=1, le=5)
    
    @validator('line_items')
    def validate_line_items(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 line items per batch request')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "line_items": [
                    {
                        "invoice_text": "Edelstahlrohr 12x1.5 mm",
                        "supplier": "MetalWorks GmbH",
                        "quantity": 50
                    },
                    {
                        "invoice_text": "Transportkosten Lieferung",
                        "line_amount": 150.00
                    }
                ],
                "top_k": 3
            }
        }


class AccountSuggestion(BaseModel):
    """Model for a single account suggestion."""
    
    account: str = Field(..., description="GL account code and name")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0, le=1)
    explanation: str = Field(..., description="Explanation for this suggestion")


class SuggestResponse(BaseModel):
    """Response model for account suggestion."""
    
    suggestions: List[AccountSuggestion] = Field(..., description="List of GL account suggestions")
    semantic_category: str = Field(..., description="Classified semantic category")
    classification_confidence: float = Field(..., description="Confidence of classification", ge=0, le=1)
    classification_method: str = Field(..., description="Classification method used")
    classification_reasoning: str = Field(..., description="Reasoning for classification")
    metadata: dict = Field(..., description="Input metadata for reference")
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "account": "4900 – Transport & Freight Costs",
                        "confidence": 0.92,
                        "explanation": "Primary account for category 'Transport' (Supplier: Express Logistics)"
                    },
                    {
                        "account": "4980 – Surcharges & Fees",
                        "confidence": 0.64,
                        "explanation": "Alternative account for category 'Transport'"
                    }
                ],
                "semantic_category": "Transport",
                "classification_confidence": 0.92,
                "classification_method": "hybrid",
                "classification_reasoning": "Rule and LLM agree: Transport-related keywords detected",
                "metadata": {
                    "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
                    "supplier": "Express Logistics",
                    "line_amount": 150.00,
                    "pos": "20"
                }
            }
        }


class FeedbackRequest(BaseModel):
    """Request model for feedback submission."""
    
    invoice_text: str = Field(..., description="Original invoice line item text")
    suggested_account: str = Field(..., description="Account that was suggested")
    actual_account: str = Field(..., description="Account that was actually used")
    user_id: Optional[str] = Field(None, description="User or tenant identifier")
    comments: Optional[str] = Field(None, description="Additional comments or context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "invoice_text": "Edelstahlrohr 12x1.5 mm",
                "suggested_account": "3000 – Raw Materials",
                "actual_account": "3000 – Raw Materials",
                "user_id": "tenant_123",
                "comments": "Correct suggestion"
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    
    status: str = Field(..., description="Status of feedback submission")
    message: str = Field(..., description="Response message")
    feedback_id: Optional[str] = Field(None, description="Unique feedback identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Feedback recorded successfully",
                "feedback_id": "fb_20260104_001"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request format",
                "details": {"field": "invoice_text", "issue": "Field required"}
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    azure_openai_available: bool = Field(..., description="Whether Azure OpenAI is configured")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "azure_openai_available": True
            }
        }
