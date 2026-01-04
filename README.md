# AI Account Coding Service

A production-ready AI service that generates General Ledger (GL) account coding suggestions for invoice line items using a hybrid approach of rule-based logic and Azure OpenAI LLM.

## 🎯 Overview

This service receives structured invoice line item data via REST API and returns:
- **Top 1-3 GL account suggestions** with confidence scores
- **Semantic classification** of the invoice item
- **Explanations** for each suggestion
- **Feedback handling** for continuous improvement

## ✨ Features

- **Hybrid Classification**: Combines rule-based keyword matching with Azure OpenAI for accurate semantic understanding
- **Deterministic Output**: Structured JSON responses suitable for ERP integration
- **API Key Authentication**: Secure access control for multi-tenant usage
- **Feedback Loop**: Captures user corrections for future model improvements
- **Azure-Ready**: Designed for deployment on Azure App Service or Container Apps
- **Extensible**: Easy to customize chart of accounts and classification rules

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│   (ERP)     │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────┐
│   FastAPI       │
│   API Layer     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Classifier     │◄────►│  Azure OpenAI    │
│  (Rule + LLM)   │      │  (GPT-4)         │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Account Mapper │
│  (GL Accounts)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │
└─────────────────┘
```

## 📋 Requirements

- Python 3.11+
- Azure OpenAI account (optional - falls back to rule-based only)
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai-account-coding-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# - Add Azure OpenAI credentials
# - Configure API keys
# - Adjust other settings as needed
```

### 3. Run the Service

```bash
# Run locally with uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up --build
```

### 4. Test the API

Visit `http://localhost:8000/docs` for interactive API documentation.

**Example request:**
```bash
curl -X POST "http://localhost:8000/api/v1/suggest" \
  -H "X-API-Key: your-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{
    "line_item": {
      "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
      "supplier": "Express Logistics",
      "line_amount": 150.00
    },
    "top_k": 3
  }'
```

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Setup Instructions](docs/SETUP_INSTRUCTIONS.md)** - Detailed setup and configuration guide
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Azure deployment instructions
- **[Example Payloads](docs/EXAMPLE_PAYLOADS.md)** - Request/response examples

## 🔑 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/api/v1/suggest` | POST | Get account suggestions for single line item |
| `/api/v1/suggest/batch` | POST | Get suggestions for multiple line items |
| `/api/v1/feedback` | POST | Submit feedback on suggestions |

## 🎯 Use Cases

1. **ERP Integration**: Automate account coding in SAP, Oracle, or other ERP systems
2. **DMS Workflows**: Pre-code documents in document management systems
3. **Invoice Processing**: Speed up accounts payable workflows
4. **Training Tool**: Assist new accountants in learning proper coding

## 🧪 Testing

```bash
# Run basic tests
python -m pytest tests/

# Test with sample data
python tests/test_engine.py
```

## 📊 Sample Data

The `data/` directory contains:
- `sample_chart_of_accounts.json` - Example GL account mappings
- `invoice_text_with_accounts.csv` - Sample training data

## 🔒 Security

- API key authentication required (configurable)
- CORS protection (configure for production)
- Input validation with Pydantic
- Rate limiting (recommended for production)

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# API Security
API_KEY_REQUIRED=true
VALID_API_KEYS=key1,key2,key3

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Logging
LOG_LEVEL=INFO
```

## 📈 Future Enhancements (V2)

- Fine-tuned model on historical data
- Multi-language support
- Advanced analytics dashboard
- Database-backed feedback storage
- Tenant-specific customization
- A/B testing framework

## 📝 License

Proprietary - All rights reserved

## 👥 Support

For questions or issues, contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: January 2026
