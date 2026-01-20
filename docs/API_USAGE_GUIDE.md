# API Usage Guide

Complete guide for developers to call the AI Account Coding API hosted on Azure.

---

## Base URL

```
https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net
```

---

## Authentication

All API requests require an API key in the `X-API-Key` header.

**Development API Key:** `dev-key-001`

```bash
curl -H "X-API-Key: dev-key-001" https://...
```

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check service status and availability.

**Example:**
```bash
curl -X GET "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_openai_available": true
}
```

---

### 2. Get Account Suggestions (Single Item)

**POST** `/api/v1/suggest`

Classify an invoice line item and get GL account suggestions.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: dev-key-001`

**Request Body:**
```json
{
  "line_item": {
    "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
    "supplier": "MAXIMUM AG",
    "quantity": 80,
    "unit_price": 14.70,
    "line_amount": 1176.00,
    "pos": "10"
  },
  "top_k": 3
}
```

**cURL Example:**
```bash
curl -X POST "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/suggest" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-001" \
  -d '{
    "line_item": {
      "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
      "supplier": "MAXIMUM AG",
      "pos": "10"
    },
    "top_k": 3
  }'
```

**Python Example:**
```python
import requests

url = "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/suggest"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "dev-key-001"
}
payload = {
    "line_item": {
        "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
        "supplier": "MAXIMUM AG",
        "pos": "10"
    },
    "top_k": 3
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "1220 – Materialvorräte",
      "confidence": 1.0,
      "explanation": "Primary account for category 'Consumables' (Pos signal: prioritized for Pos 10)"
    },
    {
      "account": "1540 – Werkzeuge und Geräte",
      "confidence": 0.672,
      "explanation": "Alternative account for category 'Consumables' (Pos signal: prioritized for Pos 10)"
    },
    {
      "account": "1200 – Waren",
      "confidence": 0.542,
      "explanation": "Alternative account for category 'Consumables'"
    }
  ],
  "semantic_category": "Consumables",
  "classification_confidence": 0.95,
  "classification_method": "rule",
  "classification_reasoning": "Matched keyword patterns: ['draht', 'binder'] → Consumables",
  "metadata": {
    "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
    "supplier": "MAXIMUM AG",
    "quantity": null,
    "unit_of_measure": null,
    "unit_price": null,
    "line_amount": null,
    "product_group": null,
    "po_reference": null,
    "pos": "10"
  }
}
```

---

### 3. Batch Account Suggestions

**POST** `/api/v1/suggest/batch`

Process multiple invoice line items in one request (up to 100 items).

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: dev-key-001`

**Request Body:**
```json
{
  "line_items": [
    {
      "invoice_text": "Palette SBB, 120x80cm",
      "pos": "999"
    },
    {
      "invoice_text": "Transportkosten",
      "pos": "20"
    },
    {
      "invoice_text": "Energiezuschlag",
      "pos": "120"
    }
  ],
  "top_k": 3
}
```

**cURL Example:**
```bash
curl -X POST "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/suggest/batch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-001" \
  -d '{
    "line_items": [
      {"invoice_text": "Palette SBB, 120x80cm", "pos": "999"},
      {"invoice_text": "Transportkosten", "pos": "20"}
    ],
    "top_k": 3
  }'
```

**Response:**
```json
[
  {
    "suggestions": [...],
    "semantic_category": "Pallets",
    "classification_confidence": 0.98,
    "classification_method": "hybrid",
    "classification_reasoning": "...",
    "metadata": {...}
  },
  {
    "suggestions": [...],
    "semantic_category": "Transport",
    "classification_confidence": 0.95,
    "classification_method": "rule",
    "classification_reasoning": "...",
    "metadata": {...}
  }
]
```

---

### 4. Submit Feedback

**POST** `/api/v1/feedback`

Submit user corrections or confirmations for suggested accounts.

**Headers:**
- `Content-Type: application/json`
- `X-API-Key: dev-key-001`

**Request Body:**
```json
{
  "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
  "suggested_account": "1220 – Materialvorräte",
  "actual_account": "1220 – Materialvorräte",
  "user_id": "vincent@company.com",
  "comments": "Correct classification"
}
```

**cURL Example:**
```bash
curl -X POST "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-001" \
  -d '{
    "invoice_text": "Rapido Drahtbinder geschweisst 10cm 1000St.",
    "suggested_account": "1220 – Materialvorräte",
    "actual_account": "1220 – Materialvorräte",
    "user_id": "vincent@company.com",
    "comments": "Correct classification"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Feedback recorded successfully",
  "feedback_id": "fb_20260120_143022"
}
```

---

## Request Fields

### LineItemRequest
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_text` | string | ✅ Yes | Invoice line item description |
| `supplier` | string | ❌ No | Supplier name or ID |
| `quantity` | float | ❌ No | Line item quantity |
| `unit_of_measure` | string | ❌ No | Unit (e.g., kg, pcs, m) |
| `unit_price` | float | ❌ No | Price per unit |
| `line_amount` | float | ❌ No | Total line amount |
| `product_group` | string | ❌ No | Product group classification |
| `po_reference` | string | ❌ No | Purchase order reference |
| `pos` | string | ❌ No | Invoice line position (improves accuracy) |

### SuggestRequest
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_item` | LineItemRequest | ✅ Yes | Invoice line item to classify |
| `top_k` | int | ❌ No | Number of suggestions (default: 3, max: 5) |

---

## Response Fields

### AccountSuggestion
| Field | Type | Description |
|-------|------|-------------|
| `account` | string | GL account code and name (e.g., "1220 – Materialvorräte") |
| `confidence` | float | Confidence score (0-1) |
| `explanation` | string | Reason for this suggestion |

### SuggestResponse
| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | AccountSuggestion[] | List of GL account suggestions (top_k items) |
| `semantic_category` | string | Classified semantic category |
| `classification_confidence` | float | Confidence of classification (0-1) |
| `classification_method` | string | Method used: `rule`, `llm`, `hybrid`, `hybrid_llm`, `hybrid_rule` |
| `classification_reasoning` | string | Explanation of classification decision |
| `metadata` | object | Input metadata for reference (includes `pos` if provided) |

---

## Classification Methods

| Method | Description |
|--------|-------------|
| `rule` | Pure rule-based classification using keyword patterns |
| `llm` | Pure LLM (Azure OpenAI) classification |
| `hybrid` | Rule and LLM agree on classification |
| `hybrid_llm` | Rule and LLM disagree; LLM wins (higher confidence) |
| `hybrid_rule` | Rule and LLM disagree; Rule wins (higher confidence) |

---

## Error Handling

### Error Response Format
```json
{
  "error": "ValidationError",
  "message": "Invalid request format",
  "details": {
    "field": "invoice_text",
    "issue": "Field required"
  }
}
```

### Common HTTP Status Codes
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created (feedback) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid API key) |
| 403 | Forbidden (invalid API key) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Best Practices

1. **Include `pos` field** — Improves accuracy through positional prioritization
2. **Provide supplier** — Helps with vendor-specific mappings
3. **Use batch endpoint** — Process multiple items efficiently (up to 100 per request)
4. **Monitor confidence** — Items with confidence < 0.7 may need manual review
5. **Submit feedback** — Helps improve the model over time
6. **Handle errors gracefully** — Check HTTP status codes and error responses

---

## Rate Limits & Costs

- **No rate limits** currently enforced (development)
- **Usage tracked** by API key for billing/monitoring
- **Azure OpenAI costs** apply per LLM classification request

---

## Interactive Demo

Try the hosted demo page:
```
https://aiacctcodingst01.z6.web.core.windows.net/demo.html
```

---

## Support

For issues or questions:
- Check [API Documentation](./API_DOCUMENTATION.md)
- Review [Example Payloads](./EXAMPLE_PAYLOADS.md)
- Contact: vincent@company.com
