"""API route handlers."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
import json
from datetime import datetime

from ..core.engine import AccountCodingEngine
from .models import (
    SuggestRequest,
    SuggestResponse,
    BatchSuggestRequest,
    FeedbackRequest,
    FeedbackResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["account-coding"])


@router.post("/suggest", response_model=SuggestResponse, status_code=status.HTTP_200_OK)
async def suggest_account(
    request: SuggestRequest,
    engine: AccountCodingEngine = Depends()
):
    """Generate GL account suggestions for a single invoice line item.
    
    This endpoint classifies the invoice line item and returns the top K
    GL account suggestions with confidence scores and explanations.
    """
    try:
        logger.info(f"Received suggestion request for: '{request.line_item.invoice_text[:50]}...'")
        
        result = engine.suggest_accounts(
            invoice_text=request.line_item.invoice_text,
            supplier=request.line_item.supplier,
            quantity=request.line_item.quantity,
            unit_of_measure=request.line_item.unit_of_measure,
            unit_price=request.line_item.unit_price,
            line_amount=request.line_item.line_amount,
            product_group=request.line_item.product_group,
            po_reference=request.line_item.po_reference,
            pos=request.line_item.pos,
            top_k=request.top_k
        )
        
        logger.info(f"Successfully generated {len(result['suggestions'])} suggestions")
        return SuggestResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing suggestion request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process suggestion: {str(e)}"
        )


@router.post("/suggest/batch", response_model=List[SuggestResponse], status_code=status.HTTP_200_OK)
async def suggest_accounts_batch(
    request: BatchSuggestRequest,
    engine: AccountCodingEngine = Depends()
):
    """Generate GL account suggestions for multiple invoice line items in batch.
    
    This endpoint processes up to 100 line items and returns suggestions for each.
    """
    try:
        logger.info(f"Received batch suggestion request for {len(request.line_items)} items")
        
        # Convert Pydantic models to dicts
        line_items_dicts = [item.dict() for item in request.line_items]
        
        results = engine.batch_suggest(
            line_items=line_items_dicts,
            top_k=request.top_k
        )
        
        # Convert results to response models
        responses = []
        for result in results:
            if "error" in result:
                # Include error in response but continue processing
                logger.warning(f"Error in batch item {result.get('line_item_index')}: {result['error']}")
                # You might want to handle errors differently - skip or return error object
                continue
            responses.append(SuggestResponse(**result))
        
        logger.info(f"Successfully processed {len(responses)} of {len(request.line_items)} items")
        return responses
        
    except Exception as e:
        logger.error(f"Error processing batch suggestion request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch suggestion: {str(e)}"
        )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on account coding suggestions.
    
    This endpoint receives user corrections and confirmations for suggested accounts.
    Feedback is stored for future model improvements.
    """
    try:
        logger.info(f"Received feedback for: '{request.invoice_text[:50]}...'")
        
        # Generate feedback ID
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store feedback (in production, this would go to a database or file)
        feedback_data = {
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "invoice_text": request.invoice_text,
            "suggested_account": request.suggested_account,
            "actual_account": request.actual_account,
            "user_id": request.user_id,
            "comments": request.comments,
            "match": request.suggested_account == request.actual_account
        }
        
        # Append to feedback log file
        try:
            with open("feedback_log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
            logger.info(f"Feedback stored with ID: {feedback_id}")
        except Exception as e:
            logger.error(f"Failed to write feedback to file: {e}")
            # Don't fail the request if logging fails
        
        return FeedbackResponse(
            status="success",
            message="Feedback recorded successfully",
            feedback_id=feedback_id
        )
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
        )


# Dependency injection for engine
def get_engine_dependency():
    """Get engine instance for dependency injection."""
    from .main import get_engine
    return Depends(get_engine)


# Update route dependencies
router.dependencies.append(get_engine_dependency())
