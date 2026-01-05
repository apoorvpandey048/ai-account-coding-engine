"""Simple FastAPI application for AI Account Coding POC."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import uuid
from datetime import datetime
from typing import Optional
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

app = FastAPI(title="GL Predictor API POC")

# Global predictor instance
predictor = None


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
    global predictor
    predictor = None
    try:
        if GLPredictor is not None:
            predictor = GLPredictor()
    except Exception:
        predictor = None


@app.get("/")
def root():
    return {"status": "ok", "service": "GL Predictor POC"}


@app.get("/health")
def health():
    """Health check endpoint for Azure monitoring."""
    return {
        "status": "healthy",
        "predictor_loaded": predictor is not None
    }


@app.post("/suggest")
def suggest(req: SuggestRequest):
    if predictor is None:
        raise HTTPException(status_code=500, detail="Predictor not available")
    raw = predictor.suggest(req.text, top_k=req.top_k)
    # normalize output
    suggestions = []
    for item in raw:
        if isinstance(item, dict):
            suggestions.append(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            suggestions.append({"account": item[0], "confidence": item[1]})
        else:
            suggestions.append({"account": str(item)})
    return {"text": req.text, "suggestions": suggestions}


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
