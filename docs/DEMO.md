# 🎯 Live Demo Guide

## Quick Demo Options

### Option 1: Local Demo with Ngrok (Recommended)

Run the API locally and expose it via ngrok for remote testing:

```powershell
# 1. Start the API server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8005

# 2. In a new terminal, start ngrok (install from https://ngrok.com)
ngrok http 8005
```

Copy the `https://xxxx.ngrok.io` URL and use it in the demo page.

### Option 2: Azure Deployment

Deploy to Azure App Service (requires Basic tier or higher):

```bash
az appservice plan create --name demo-plan --resource-group ai-account-coding --sku B1 --is-linux
az webapp create --resource-group ai-account-coding --plan demo-plan --name your-app-name --runtime "PYTHON|3.11"
az webapp deploy --name your-app-name --resource-group ai-account-coding --src-path deploy.zip --type zip
```

## 📱 Access the Demo

Open the interactive demo at: **https://YOUR-GITHUB-USERNAME.github.io/ai-account-coding-engine/**

### Demo API Key

Use this key for testing: `dev-key-001`

### Example Requests

**Health Check**
```bash
curl https://your-api-host/health
```

**Get GL Suggestion**
```bash
curl -X POST https://your-api-host/api/v1/suggest \
  -H "X-API-Key: dev-key-001" \
  -H "Content-Type: application/json" \
  -d '{
    "line_item": {
      "invoice_text": "Palette SBB, 120x80cm",
      "supplier": "VendorX",
      "quantity": "1",
      "unit_price": 21.0,
      "line_amount": 21.0
    },
    "top_k": 3
  }'
```

## 🎨 Features Demonstrated

- ✅ Real-time GL account suggestions
- ✅ Semantic classification with confidence scores
- ✅ Batch processing capabilities
- ✅ Feedback collection for continuous improvement
- ✅ API key authentication
- ✅ Professional UI with responsive design
