# Setup Instructions

Complete guide for setting up and running the AI Account Coding Service.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Running the Service](#running-the-service)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.11 or higher**
  ```bash
  python --version  # Should be 3.11+
  ```

- **pip** (Python package manager)
  ```bash
  pip --version
  ```

### Optional

- **Azure OpenAI Access** (for LLM-based classification)
  - Azure subscription
  - Azure OpenAI resource with GPT-4 deployment
  
- **Docker** (for containerized deployment)
  ```bash
  docker --version
  docker-compose --version
  ```

- **Git** (for version control)
  ```bash
  git --version
  ```

---

## Local Development Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd ai-account-coding-engine
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Expected packages:**
- fastapi
- uvicorn
- pydantic
- pydantic-settings
- openai
- python-dotenv
- gunicorn

### Step 4: Verify Installation

```bash
python -c "import fastapi; import openai; print('All packages installed successfully')"
```

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example file
cp .env.example .env

# Or on Windows
copy .env.example .env
```

### Step 2: Configure Settings

Edit `.env` file with your settings:

```env
# Service Configuration
SERVICE_NAME=ai-account-coding-service
ENVIRONMENT=development
LOG_LEVEL=INFO

# API Security
API_KEY_REQUIRED=true
VALID_API_KEYS=dev-key-001,dev-key-002

# Azure OpenAI Configuration (optional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Feedback Storage
FEEDBACK_STORAGE_TYPE=file
FEEDBACK_FILE_PATH=feedback_log.jsonl
```

### Step 3: Configure Azure OpenAI (Optional)

If you want to use LLM-based classification:

1. **Create Azure OpenAI Resource:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Note the endpoint URL

2. **Deploy GPT-4 Model:**
   - In Azure OpenAI Studio, deploy a GPT-4 model
   - Note the deployment name

3. **Get API Key:**
   - Go to Keys and Endpoint in Azure Portal
   - Copy one of the API keys

4. **Update .env:**
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_KEY=abc123...
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```

**Note:** If Azure OpenAI is not configured, the service will work in **rule-based mode only**.

### Step 4: Generate API Keys

For development, you can use simple keys:

```env
VALID_API_KEYS=dev-key-001,test-key-123,local-key-456
```

For production, generate secure keys:

```bash
# Generate secure random API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Running the Service

### Option 1: Run with Uvicorn (Development)

```bash
# From project root, with venv activated
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Flags:**
- `--reload`: Auto-reload on code changes
- `--host 0.0.0.0`: Accept connections from any IP
- `--port 8000`: Run on port 8000

**Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Option 2: Run with Docker

```bash
# Build and run
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 3: Run with Gunicorn (Production-like)

```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

---

## Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_openai_available": true
}
```

### 2. Test API with cURL

```bash
curl -X POST "http://localhost:8000/api/v1/suggest" \
  -H "X-API-Key: dev-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "line_item": {
      "invoice_text": "Edelstahlrohr 12x1.5 mm"
    },
    "top_k": 3
  }'
```

### 3. Interactive API Documentation

Open in browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 4. Run Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python tests/test_engine.py
```

### 5. Test with Sample Data

```bash
# Test with provided CSV data
python -c "
import pandas as pd
import requests

df = pd.read_csv('data/invoice_text_with_accounts.csv')
url = 'http://localhost:8000/api/v1/suggest'
headers = {'X-API-Key': 'dev-key-001', 'Content-Type': 'application/json'}

for idx, row in df.head(5).iterrows():
    payload = {
        'line_item': {'invoice_text': row['extracted_invoice_text']},
        'top_k': 3
    }
    resp = requests.post(url, json=payload, headers=headers)
    print(f'{row[\"extracted_invoice_text\"][:50]} -> {resp.json()[\"suggestions\"][0][\"account\"]}')
"
```

---

## Troubleshooting

### Issue: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: Port Already in Use

**Error:**
```
Error: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn src.api.main:app --port 8001
```

### Issue: Azure OpenAI Connection Failed

**Error:**
```
Failed to connect to Azure OpenAI
```

**Solution:**
1. Check endpoint URL format:
   ```
   https://your-resource-name.openai.azure.com/
   ```
   
2. Verify API key is correct

3. Check deployment name matches your GPT-4 deployment

4. Test connection:
   ```python
   from openai import AzureOpenAI
   
   client = AzureOpenAI(
       api_key="your-key",
       api_version="2024-02-15-preview",
       azure_endpoint="https://your-resource.openai.azure.com/"
   )
   
   # Test simple completion
   response = client.chat.completions.create(
       model="gpt-4",  # Your deployment name
       messages=[{"role": "user", "content": "Hello"}]
   )
   print(response.choices[0].message.content)
   ```

### Issue: API Key Authentication Fails

**Error:**
```
{"error": "Unauthorized", "message": "Invalid API Key"}
```

**Solution:**
1. Check API key in request header:
   ```bash
   -H "X-API-Key: your-key-here"
   ```

2. Verify key exists in `.env`:
   ```env
   VALID_API_KEYS=key1,key2,key3
   ```

3. Restart service after changing `.env`

4. For testing, disable API key requirement:
   ```env
   API_KEY_REQUIRED=false
   ```

### Issue: Rule-Based Only Mode

**Symptom:**
```
classification_method: "rule"  (never "llm" or "hybrid")
```

**Solution:**
This means Azure OpenAI is not configured or connection failed. Check:

1. Environment variables are set
2. Azure OpenAI service is accessible
3. Check logs for connection errors:
   ```bash
   tail -f logs/service_*.log
   ```

### Issue: Low Confidence Scores

**Symptom:**
```json
{
  "confidence": 0.3,
  "semantic_category": "Other"
}
```

**Solution:**
1. **Add more context** - Include supplier, product_group
2. **Check invoice text** - Should be descriptive
3. **Customize rules** - Edit `src/core/classifier.py` keywords
4. **Update chart of accounts** - Adjust category mappings
5. **Enable LLM** - Configure Azure OpenAI for better accuracy

### Issue: Docker Build Fails

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt"
```

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check Dockerfile syntax
# Ensure requirements.txt exists
ls -la requirements.txt
```

---

## Logs

### Log Locations

- **Console output**: Real-time logs in terminal
- **File logs**: `logs/service_YYYYMMDD.log`

### Log Levels

Configure in `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### View Logs

```bash
# Tail current log file
tail -f logs/service_$(date +%Y%m%d).log

# Search logs
grep "ERROR" logs/service_*.log
```

---

## Next Steps

Once setup is complete:

1. ✅ **Read [API Documentation](API_DOCUMENTATION.md)** for endpoint details
2. ✅ **Review [Deployment Guide](DEPLOYMENT_GUIDE.md)** for production deployment
3. ✅ **Check [Example Payloads](EXAMPLE_PAYLOADS.md)** for integration examples
4. ✅ **Customize chart of accounts** in `src/core/mapper.py`
5. ✅ **Add custom rules** in `src/core/classifier.py`

---

## Support

For issues not covered here, check:
- Service logs in `logs/` directory
- FastAPI error responses
- Azure OpenAI service status

---

**Last Updated:** January 2026
