"""Simple FastAPI application for AI Account Coding POC."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict
import sys
from pathlib import Path

# Add root directory to path for gl_predictor import
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

try:
    from gl_predictor import GLPredictor
except Exception as e:
    print(f"Warning: Could not import GLPredictor: {e}")
    GLPredictor = None

# Azure OpenAI imports
try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: openai package not available")
    OPENAI_AVAILABLE = False
    AzureOpenAI = None

app = FastAPI(title="GL Predictor API POC")

# Global instances
predictor = None
azure_openai_client = None


class SuggestRequest(BaseModel):
    text: str
    top_k: Optional[int] = 3


class FeedbackRequest(BaseModel):
    text: str
    selected_account: str
    confidence: Optional[float] = None
    notes: Optional[str] = None


@app.on_event("startup")
def startup_event():
    global predictor, azure_openai_client
    
    # Initialize rule-based predictor
    predictor = None
    try:
        if GLPredictor is not None:
            predictor = GLPredictor()
            print("✓ GLPredictor loaded")
    except Exception as e:
        print(f"✗ GLPredictor failed: {e}")
    
    # Initialize Azure OpenAI client
    azure_openai_client = None
    if OPENAI_AVAILABLE:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        if endpoint and api_key:
            try:
                azure_openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                print("✓ Azure OpenAI client initialized")
            except Exception as e:
                print(f"✗ Azure OpenAI init failed: {e}")
        else:
            print("✗ Azure OpenAI credentials not configured")


@app.get("/")
def root():
    return {"status": "ok", "service": "GL Predictor POC"}


@app.get("/health")
def health():
    """Health check endpoint for Azure monitoring."""
    return {
        "status": "healthy",
        "predictor_loaded": predictor is not None,
        "azure_openai_available": azure_openai_client is not None
    }


@app.post("/suggest")
def suggest(req: SuggestRequest):
    suggestions = []
    method_used = "none"
    
    # Step 1: Try rule-based predictor first
    if predictor is not None:
        try:
            raw = predictor.suggest(req.text, top_k=req.top_k)
            for item in raw:
                if isinstance(item, dict):
                    suggestions.append(item)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    suggestions.append({"account": item[0], "confidence": item[1], "explanation": item[2] if len(item) > 2 else "Rule-based match"})
                else:
                    suggestions.append({"account": str(item), "confidence": 0.1, "explanation": "Fallback"})
            method_used = "rule-based"
        except Exception as e:
            print(f"Rule-based predictor error: {e}")
    
    # Step 2: If no high-confidence suggestions, use Azure OpenAI
    best_confidence = max([s.get("confidence", 0) for s in suggestions], default=0)
    
    if best_confidence < 0.5 and azure_openai_client is not None:
        try:
            ai_suggestions = get_ai_suggestions(req.text, req.top_k)
            if ai_suggestions:
                suggestions = ai_suggestions
                method_used = "ai"
        except Exception as e:
            print(f"Azure OpenAI error: {e}")
            # Keep rule-based suggestions as fallback
    
    if not suggestions:
        raise HTTPException(status_code=500, detail="No suggestions available")
    
    return {
        "text": req.text,
        "suggestions": suggestions[:req.top_k],
        "method": method_used
    }


def get_ai_suggestions(invoice_text: str, top_k: int = 3) -> List[Dict]:
    """Get GL account suggestions from Azure OpenAI GPT-4.1-mini."""
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-1-mini")
    max_tokens = int(os.getenv("AZURE_OPENAI_MAX_OUTPUT_TOKENS", "1000"))
    temperature = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.3"))
    
    prompt = f"""You are an accounting expert. Analyze this invoice line item and suggest the top {top_k} GL accounts.

Invoice text: "{invoice_text}"

Provide your response as a JSON array with exactly {top_k} suggestions, each with:
- "account": GL account code and name (e.g., "6200 - Cloud Services")
- "confidence": number between 0 and 1
- "explanation": brief reason (1 sentence)

Example format:
[
  {{"account": "6200 - IT Services", "confidence": 0.85, "explanation": "Cloud hosting is an IT infrastructure expense."}},
  {{"account": "5400 - Technology", "confidence": 0.75, "explanation": "Alternative technology expense category."}},
  {{"account": "6100 - Professional Services", "confidence": 0.60, "explanation": "Could be categorized as external service."}}
]

Respond with ONLY the JSON array, no other text."""
    
    try:
        response = azure_openai_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a precise accounting assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content.strip()
        # Parse JSON response
        import json as json_lib
        suggestions = json_lib.loads(content)
        
        return suggestions[:top_k]
    
    except Exception as e:
        print(f"AI suggestion error: {e}")
        return []


@app.post("/feedback")
def feedback(fb: FeedbackRequest):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "text": fb.text,
        "selected_account": fb.selected_account,
        "confidence": fb.confidence,
        "notes": fb.notes,
    }
    # write to local file for now
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", "feedback.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write feedback: {e}")

    # optional: try upload to Azure Blob if configured
    account = os.getenv("STORAGE_ACCOUNT_NAME")
    container = os.getenv("CONTAINER_FEEDBACK", "feedback")
    if account:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobClient
            cred = DefaultAzureCredential()
            blob_name = f"feedback/{entry['id']}.json"
            client = BlobClient(account_url=f"https://{account}.blob.core.windows.net", container_name=container, blob_name=blob_name, credential=cred)
            client.upload_blob(json.dumps(entry, ensure_ascii=False), overwrite=True)
        except Exception:
            # non-fatal — feedback persisted locally
            pass

    return {"status": "ok", "id": entry["id"]}
