# 🚀 Quick Start Guide

## Run Locally

### Prerequisites
- Python 3.11+
- pip

### Steps

```powershell
# 1. Navigate to project directory
cd ai-account-coding-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the API server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8005 --reload
```

Server will run at `http://localhost:8005`

### Test the API

```powershell
# Health check
curl http://localhost:8005/health

# Get GL suggestion
curl -X POST http://localhost:8005/api/v1/suggest `
  -H "X-API-Key: dev-key-001" `
  -H "Content-Type: application/json" `
  -d '{\"line_item\": {\"invoice_text\": \"Palette SBB\", \"supplier\": \"VendorX\"}, \"top_k\": 3}'
```

## 🌐 Make It Publicly Accessible

### Option 1: Using Ngrok (Recommended for Demo)

1. **Install ngrok** from https://ngrok.com/download

2. **Start your local server** (step 3 above)

3. **In a new terminal, run:**
   ```powershell
   ngrok http 8005
   ```

4. **Copy the public URL** (e.g., `https://abc123.ngrok.io`)

5. **Open the demo page** at: https://apoorvpandey048.github.io/ai-account-coding-engine/

6. **Enter the ngrok URL** in the "API Host URL" field and use API key: `dev-key-001`

### Option 2: Using Cloudflared (Alternative)

```powershell
# Install cloudflare tunnel
winget install --id Cloudflare.cloudflared

# Create tunnel
cloudflared tunnel --url http://localhost:8005
```

Copy the provided `*.trycloudflare.com` URL to the demo page.

## 🎨 Access the Demo

**Live Demo:** https://apoorvpandey048.github.io/ai-account-coding-engine/

**Demo API Key:** `dev-key-001`

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/suggest` | POST | Get GL account suggestions for a single line item |
| `/api/v1/suggest/batch` | POST | Process multiple line items |
| `/api/v1/feedback` | POST | Submit feedback for model improvement |

## 🔧 Configuration

Create a `.env` file (optional for local testing):

```env
API_KEY_REQUIRED=true
VALID_API_KEYS=dev-key-001,prod-key-002
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
```

## 📖 Full Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Setup Instructions](docs/SETUP_INSTRUCTIONS.md)

## 💡 Need Help?

Check the [full README](README.md) for detailed information.
