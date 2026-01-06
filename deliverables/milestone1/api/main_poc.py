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
import difflib

# Add root directory to path for imports
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import configuration
from src.utils.config import get_settings
settings = get_settings()

try:
    from gl_predictor import GLPredictor
    print("[OK] GLPredictor module imported successfully")
except Exception as e:
    print(f"[WARN] Could not import GLPredictor: {e}")
    import traceback
    traceback.print_exc()
    GLPredictor = None

# Import Milestone 1 core engine
try:
    from src.core.engine import AccountCodingEngine
    from src.core.classifier import SemanticClassifier
    from src.core.mapper import AccountMapper
    print("[OK] Core engine modules imported successfully")
except Exception as e:
    print(f"[WARN] Could not import core engine: {e}")
    import traceback
    traceback.print_exc()
    AccountCodingEngine = None

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
core_engine = None


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
    global predictor, azure_openai_client, core_engine
    
    print("=" * 60)
    print("Starting up GL Predictor API...")
    print("=" * 60)
    
    # Initialize rule-based predictor
    predictor = None
    try:
        if GLPredictor is not None:
            predictor = GLPredictor()
            print("[OK] GLPredictor loaded successfully")
        else:
            print("[ERROR] GLPredictor module was not imported")
    except Exception as e:
        print(f"[ERROR] GLPredictor failed to initialize: {e}")
        import traceback
        traceback.print_exc()
    
    # Initialize Azure OpenAI client
    azure_openai_client = None
    if OPENAI_AVAILABLE:
        endpoint = settings.AZURE_OPENAI_ENDPOINT
        api_key = settings.AZURE_OPENAI_KEY
        api_version = settings.AZURE_OPENAI_API_VERSION
        
        if endpoint and api_key:
            try:
                azure_openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                print(f"[OK] Azure OpenAI client initialized")
                print(f"     Endpoint: {endpoint}")
                print(f"     Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
                print(f"     Model: {settings.AZURE_OPENAI_MODEL}")
                print(f"     Temperature: {settings.AZURE_OPENAI_TEMPERATURE}")
            except Exception as e:
                print(f"[ERROR] Azure OpenAI init failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[WARN] Azure OpenAI not configured (missing endpoint or key)")
            print(f"     Endpoint: {'SET' if endpoint else 'MISSING'}")
            print(f"     API Key: {'SET' if api_key else 'MISSING'}")
            missing = []
            if not endpoint: missing.append("AZURE_OPENAI_ENDPOINT")
            if not api_key: missing.append("AZURE_OPENAI_KEY")
            print(f"[WARN] Azure OpenAI credentials not configured (missing: {', '.join(missing)})")
    
    # Initialize Milestone 1 core engine
    core_engine = None
    try:
        if AccountCodingEngine is not None:
            core_engine = AccountCodingEngine(azure_openai_client=azure_openai_client)
            print("[OK] Core engine initialized successfully")
        else:
            print("[WARN] Core engine modules not imported")
    except Exception as e:
        print(f"[ERROR] Core engine init failed: {e}")
        import traceback
        traceback.print_exc()



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


@app.get("/debug/ai-test")
def test_ai():
    """Debug endpoint to test Azure OpenAI directly."""
    if azure_openai_client is None:
        return {"error": "Azure OpenAI client not available"}
    
    try:
        result = get_ai_suggestions("office supplies paper", top_k=2)
        return {"success": True, "suggestions": result}
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/suggest")
def suggest(req: SuggestRequest):
    # Validate text is not empty
    if not req.text or req.text.strip() == "":
        raise HTTPException(status_code=400, detail="Text field cannot be empty")
    
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
    
    # Step 2: If no high-confidence suggestions, use semantic classifier
    best_confidence = max([s.get("confidence", 0) for s in suggestions], default=0)
    ai_error = None
    
    # Use core engine if confidence < 0.7 and OpenAI not available, OR if confidence < 0.5 with OpenAI
    if best_confidence < 0.7 and azure_openai_client is None and core_engine is not None:
        try:
            result = core_engine.suggest_accounts(req.text, top_k=req.top_k)
            if result and result.get("suggestions"):
                # Convert core engine format to API format
                suggestions = result["suggestions"]
                method_used = f"semantic-{result.get('metadata', {}).get('method', 'unknown')}"
            else:
                ai_error = "Core engine returned no suggestions"
        except Exception as e:
            print(f"Core engine error: {e}")
            import traceback
            traceback.print_exc()
            ai_error = f"Core engine: {type(e).__name__}: {str(e)}"
    elif best_confidence < 0.7 and azure_openai_client is not None:
        # Use Azure OpenAI if available
        try:
            ai_suggestions = get_ai_suggestions(req.text, req.top_k)
            if ai_suggestions:
                suggestions = ai_suggestions
                method_used = "ai"
            else:
                ai_error = "AI returned empty result"
        except Exception as e:
            print(f"Azure OpenAI error: {e}")
            import traceback
            traceback.print_exc()
            ai_error = f"{type(e).__name__}: {str(e)}"
            # Keep rule-based suggestions as fallback
    
    if not suggestions:
        raise HTTPException(status_code=500, detail="No suggestions available")
    
    # Calculate final confidence from returned suggestions
    final_confidence = max([s.get("confidence", 0) for s in suggestions[:req.top_k]], default=0)
    
    response = {
        "text": req.text,
        "suggestions": suggestions[:req.top_k],
        "method": method_used,
        "debug": {
            "initial_confidence": best_confidence,
            "final_confidence": final_confidence,
            "ai_client_available": azure_openai_client is not None,
            "should_use_ai": best_confidence < 0.5 and azure_openai_client is not None,
            "ai_error": ai_error
        }
    }
    return response


def get_ai_suggestions(invoice_text: str, top_k: int = 3) -> List[Dict]:
    """Get GL account suggestions from Azure OpenAI GPT-4.1-mini."""
    deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
    # GPT-4.1-mini supports max 32768 completion tokens
    max_tokens = min(settings.AZURE_OPENAI_MAX_OUTPUT_TOKENS, 32768)
    temperature = settings.AZURE_OPENAI_TEMPERATURE

    # Build allowed accounts list from the rule-based predictor (training data)
    allowed_accounts = []
    try:
        if predictor is not None and hasattr(predictor, 'df'):
            allowed_accounts = list(predictor.df['suggested_account'].unique())
    except Exception:
        allowed_accounts = []

    # Fallback: try to load from a file if predictor not available
    if not allowed_accounts:
        try:
            import pandas as _pd
            _df = _pd.read_csv('data/train_split.csv')
            allowed_accounts = list(_df['suggested_account'].unique())
        except Exception:
            allowed_accounts = []

    # Compose prompt that includes a strict list of valid accounts and an instruction
    accounts_list_text = "\n".join([f"- {a}" for a in allowed_accounts]) if allowed_accounts else "(no accounts provided)"

    prompt = f"""You are an accounting assistant. Analyze this invoice line item and suggest the top {top_k} GL accounts.

Valid accounts (exact strings) that you MUST choose from (do NOT invent new accounts):
{accounts_list_text}

Invoice text: "{invoice_text}"

Return a JSON array with exactly {top_k} suggestions. Each suggestion must be an object with:
- "account": exact account string from the valid accounts list above
- "confidence": number between 0 and 1
- "explanation": one short sentence explaining why

Respond with ONLY the JSON array, and nothing else. If you cannot find {top_k} valid accounts, return as many as you can but not more than {top_k}.
"""

    try:
        response = azure_openai_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a precise accounting assistant. Always respond with valid JSON only and choose only from the provided valid accounts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        content = response.choices[0].message.content.strip()
        import json as json_lib
        try:
            suggestions = json_lib.loads(content)
        except Exception:
            # If model returned extraneous text, try to extract JSON substring
            import re
            m = re.search(r"(\[.*\])", content, re.S)
            if m:
                suggestions = json_lib.loads(m.group(1))
            else:
                raise

        # Validate suggestions: ensure accounts are in allowed_accounts; attempt fuzzy match for minor differences
        validated = []
        for s in suggestions:
            acct = s.get('account') if isinstance(s, dict) else None
            if acct and acct in allowed_accounts:
                validated.append(s)
            else:
                # attempt fuzzy matching
                if acct and allowed_accounts:
                    close = difflib.get_close_matches(acct, allowed_accounts, n=1, cutoff=0.7)
                    if close:
                        s['account'] = close[0]
                        validated.append(s)
                        continue
                # discard non-matching suggestion
        
        return validated[:top_k]

    except Exception as e:
        print(f"AI suggestion error: {e}")
        import traceback
        traceback.print_exc()
        raise


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

    return {
        "status": "ok", 
        "id": entry["id"], 
        "timestamp": entry["timestamp"],
        "text": entry["text"],
        "selected_account": entry["selected_account"]
    }
