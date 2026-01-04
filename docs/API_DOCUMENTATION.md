# API Documentation

Complete API reference for the AI Account Coding Service.

## Base URL

```
Development: http://localhost:8000
Production: https://your-service.azurewebsites.net
```

## Authentication

All API endpoints (except `/` and `/health`) require an API key passed in the header:

```
X-API-Key: your-api-key-here
```

## Endpoints

### 1. Root Endpoint

**GET** `/`

Returns basic service information.

**Response:**
```json
{
  "service": "AI Account Coding Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### 2. Health Check

**GET** `/health`

Check service health and configuration.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_openai_available": true
}
```

---

### 3. Suggest Account (Single)

**POST** `/api/v1/suggest`

Generate GL account suggestions for a single invoice line item.

**Headers:**
- `X-API-Key: your-api-key` (required)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "line_item": {
    "invoice_text": "Edelstahlrohr 12x1.5 mm",
    "supplier": "MetalWorks GmbH",
    "quantity": 50,
    "unit_of_measure": "pcs",
    "unit_price": 12.50,
    "line_amount": 625.00,
    "product_group": "Metal Pipes",
    "po_reference": "PO-2026-001"
  },
  "top_k": 3
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `line_item.invoice_text` | string | ✅ Yes | Invoice line item description |
| `line_item.supplier` | string | ❌ No | Supplier name or ID |
| `line_item.quantity` | number | ❌ No | Item quantity |
| `line_item.unit_of_measure` | string | ❌ No | Unit (kg, pcs, m, etc.) |
| `line_item.unit_price` | number | ❌ No | Price per unit |
| `line_item.line_amount` | number | ❌ No | Total line amount |
| `line_item.product_group` | string | ❌ No | Product group |
| `line_item.po_reference` | string | ❌ No | Purchase order reference |
| `top_k` | integer | ❌ No | Number of suggestions (1-5, default: 3) |

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "account": "3000 – Raw Materials",
      "confidence": 0.92,
      "explanation": "Primary account for category 'Material' (Supplier: MetalWorks GmbH)"
    },
    {
      "account": "4200 – Consumables",
      "confidence": 0.64,
      "explanation": "Alternative account for category 'Material'"
    }
  ],
  "semantic_category": "Material",
  "classification_confidence": 0.92,
  "classification_method": "hybrid",
  "classification_reasoning": "Rule and LLM agree: Material-related keywords detected",
  "metadata": {
    "invoice_text": "Edelstahlrohr 12x1.5 mm",
    "supplier": "MetalWorks GmbH",
    "quantity": 50,
    "unit_of_measure": "pcs",
    "unit_price": 12.50,
    "line_amount": 625.00,
    "product_group": "Metal Pipes",
    "po_reference": "PO-2026-001"
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array | List of account suggestions |
| `suggestions[].account` | string | GL account code and name |
| `suggestions[].confidence` | number | Confidence score (0-1) |
| `suggestions[].explanation` | string | Explanation for this suggestion |
| `semantic_category` | string | Classified semantic category |
| `classification_confidence` | number | Classification confidence (0-1) |
| `classification_method` | string | Method used: `rule`, `llm`, or `hybrid` |
| `classification_reasoning` | string | Reasoning for classification |
| `metadata` | object | Original input data for reference |

---

### 4. Suggest Account (Batch)

**POST** `/api/v1/suggest/batch`

Process multiple invoice line items in a single request (max 100 items).

**Headers:**
- `X-API-Key: your-api-key` (required)
- `Content-Type: application/json`

**Request Body:**
```json
{
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
```

**Response (200 OK):**

Array of suggestion responses (same format as single suggest endpoint):

```json
[
  {
    "suggestions": [...],
    "semantic_category": "Material",
    "classification_confidence": 0.92,
    ...
  },
  {
    "suggestions": [...],
    "semantic_category": "Transport",
    "classification_confidence": 0.88,
    ...
  }
]
```

**Limits:**
- Maximum 100 line items per request
- Items with errors are skipped (logged)

---

### 5. Submit Feedback

**POST** `/api/v1/feedback`

Submit feedback on account coding suggestions for future improvements.

**Headers:**
- `X-API-Key: your-api-key` (required)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "invoice_text": "Edelstahlrohr 12x1.5 mm",
  "suggested_account": "3000 – Raw Materials",
  "actual_account": "3000 – Raw Materials",
  "user_id": "tenant_123",
  "comments": "Correct suggestion"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `invoice_text` | string | ✅ Yes | Original invoice line text |
| `suggested_account` | string | ✅ Yes | Account that was suggested |
| `actual_account` | string | ✅ Yes | Account that was actually used |
| `user_id` | string | ❌ No | User or tenant identifier |
| `comments` | string | ❌ No | Additional context or notes |

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Feedback recorded successfully",
  "feedback_id": "fb_20260104_143052"
}
```

---

## Error Responses

All endpoints may return error responses in this format:

**400 Bad Request:**
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

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "API Key required"
}
```

**403 Forbidden:**
```json
{
  "error": "Forbidden",
  "message": "Invalid API Key"
}
```

**500 Internal Server Error:**
```json
{
  "error": "InternalServerError",
  "message": "Failed to process suggestion",
  "details": {
    "error": "Connection timeout to Azure OpenAI"
  }
}
```

---

## Rate Limiting

*Recommended for production:*

- 100 requests per minute per API key
- 1000 requests per hour per API key
- Batch requests count as 1 request

---

## Semantic Categories

The service classifies items into these categories:

| Category | Examples |
|----------|----------|
| **Material** | Steel pipes, metal sheets, raw materials |
| **Consumables** | Screws, nails, seals, packaging |
| **Transport** | Freight costs, delivery fees, shipping |
| **Surcharge** | Small quantity fees, energy surcharges |
| **IT & Software** | Software licenses, SaaS subscriptions |
| **Tools** | Power tools, equipment, machinery |
| **Service** | Maintenance, repairs, consulting |
| **Safety** | Safety helmets, protective gear |
| **Operating Supplies** | Oils, lubricants, coolants |
| **Other** | Uncategorized items |

---

## Best Practices

1. **Always provide `invoice_text`** - This is the minimum required field
2. **Include supplier information** - Improves accuracy for supplier-specific patterns
3. **Use batch endpoint** - More efficient for processing multiple items
4. **Submit feedback** - Helps improve future suggestions
5. **Handle errors gracefully** - Implement retry logic for transient failures
6. **Cache responses** - For identical requests within same session

---

## Code Examples

### Python Example

```python
import requests

API_URL = "http://localhost:8000/api/v1/suggest"
API_KEY = "your-api-key-here"

def get_account_suggestions(invoice_text, supplier=None):
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "line_item": {
            "invoice_text": invoice_text,
            "supplier": supplier
        },
        "top_k": 3
    }
    
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Usage
result = get_account_suggestions(
    "Edelstahlrohr 12x1.5 mm",
    supplier="MetalWorks GmbH"
)

print(f"Top suggestion: {result['suggestions'][0]['account']}")
print(f"Confidence: {result['suggestions'][0]['confidence']}")
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/suggest" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "line_item": {
      "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
      "supplier": "Express Logistics"
    },
    "top_k": 3
  }'
```

### JavaScript Example

```javascript
const API_URL = 'http://localhost:8000/api/v1/suggest';
const API_KEY = 'your-api-key-here';

async function getAccountSuggestions(invoiceText, supplier) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      line_item: {
        invoice_text: invoiceText,
        supplier: supplier
      },
      top_k: 3
    })
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return await response.json();
}

// Usage
getAccountSuggestions('Edelstahlrohr 12x1.5 mm', 'MetalWorks GmbH')
  .then(result => {
    console.log('Top suggestion:', result.suggestions[0].account);
    console.log('Confidence:', result.suggestions[0].confidence);
  });
```

---

## Interactive Documentation

For interactive API testing, visit the automatically generated Swagger UI:

```
http://localhost:8000/docs
```

Or ReDoc:

```
http://localhost:8000/redoc
```
