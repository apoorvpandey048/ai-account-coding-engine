# Example Payloads

Real-world examples of API requests and responses for the AI Account Coding Service.

## Table of Contents

1. [Basic Examples](#basic-examples)
2. [Advanced Examples](#advanced-examples)
3. [Batch Processing](#batch-processing)
4. [Feedback Examples](#feedback-examples)
5. [Error Scenarios](#error-scenarios)

---

## Basic Examples

### Example 1: Material Purchase

**Request:**
```json
POST /api/v1/suggest
X-API-Key: your-api-key
Content-Type: application/json

{
  "line_item": {
    "invoice_text": "Edelstahlrohr 12x1.5 mm"
  },
  "top_k": 3
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "3000 – Raw Materials",
      "confidence": 0.920,
      "explanation": "Primary account for category 'Material'"
    },
    {
      "account": "4200 – Consumables",
      "confidence": 0.644,
      "explanation": "Alternative account for category 'Material'"
    }
  ],
  "semantic_category": "Material",
  "classification_confidence": 0.920,
  "classification_method": "hybrid",
  "classification_reasoning": "Rule and LLM agree: Material-related keywords detected",
  "metadata": {
    "invoice_text": "Edelstahlrohr 12x1.5 mm",
    "supplier": null,
    "quantity": null,
    "unit_of_measure": null,
    "unit_price": null,
    "line_amount": null,
    "product_group": null,
    "po_reference": null
  }
}
```

---

### Example 2: Transport Costs

**Request:**
```json
{
  "line_item": {
    "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
    "supplier": "Express Logistics AG",
    "line_amount": 150.00
  },
  "top_k": 2
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "4900 – Transport & Freight Costs",
      "confidence": 0.950,
      "explanation": "Primary account for category 'Transport' (Supplier: Express Logistics AG)"
    },
    {
      "account": "4980 – Surcharges & Fees",
      "confidence": 0.665,
      "explanation": "Alternative account for category 'Transport'"
    }
  ],
  "semantic_category": "Transport",
  "classification_confidence": 0.950,
  "classification_method": "rule",
  "classification_reasoning": "Matched 2 keyword(s) for Transport",
  "metadata": {
    "invoice_text": "Transportkosten Lieferung Baustelle Zürich",
    "supplier": "Express Logistics AG",
    "line_amount": 150.00
  }
}
```

---

### Example 3: IT Services

**Request:**
```json
{
  "line_item": {
    "invoice_text": "Microsoft Office 365 Business Standard - Annual License",
    "supplier": "Microsoft Corporation",
    "quantity": 10,
    "unit_of_measure": "licenses",
    "unit_price": 149.99,
    "line_amount": 1499.90
  },
  "top_k": 3
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "6500 – IT & Software Expenses",
      "confidence": 0.880,
      "explanation": "Primary account for category 'IT & Software' (Supplier: Microsoft Corporation)"
    },
    {
      "account": "6000 – External Services",
      "confidence": 0.616,
      "explanation": "Alternative account for category 'IT & Software'"
    }
  ],
  "semantic_category": "IT & Software",
  "classification_confidence": 0.880,
  "classification_method": "hybrid",
  "classification_reasoning": "LLM override: Software license identified from invoice text",
  "metadata": {
    "invoice_text": "Microsoft Office 365 Business Standard - Annual License",
    "supplier": "Microsoft Corporation",
    "quantity": 10,
    "unit_of_measure": "licenses",
    "unit_price": 149.99,
    "line_amount": 1499.90
  }
}
```

---

## Advanced Examples

### Example 4: With Full Context

**Request:**
```json
{
  "line_item": {
    "invoice_text": "Schrauben M6 Edelstahl 500St",
    "supplier": "TechnoScrew GmbH",
    "quantity": 500,
    "unit_of_measure": "pcs",
    "unit_price": 0.15,
    "line_amount": 75.00,
    "product_group": "Fasteners",
    "po_reference": "PO-2026-12345"
  },
  "top_k": 3
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "4200 – Consumables",
      "confidence": 0.920,
      "explanation": "Primary account for category 'Consumables' (Supplier: TechnoScrew GmbH)"
    },
    {
      "account": "3000 – Raw Materials",
      "confidence": 0.644,
      "explanation": "Alternative account for category 'Consumables'"
    },
    {
      "account": "6100 – Tools & Equipment",
      "confidence": 0.276,
      "explanation": "Fallback account for uncertain classification"
    }
  ],
  "semantic_category": "Consumables",
  "classification_confidence": 0.920,
  "classification_method": "rule",
  "classification_reasoning": "Matched 3 keyword(s) for Consumables",
  "metadata": {
    "invoice_text": "Schrauben M6 Edelstahl 500St",
    "supplier": "TechnoScrew GmbH",
    "quantity": 500,
    "unit_of_measure": "pcs",
    "unit_price": 0.15,
    "line_amount": 75.00,
    "product_group": "Fasteners",
    "po_reference": "PO-2026-12345"
  }
}
```

---

### Example 5: Ambiguous Item (Low Confidence)

**Request:**
```json
{
  "line_item": {
    "invoice_text": "Sonderanfertigung nach Zeichnung"
  },
  "top_k": 3
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "account": "6000 – External Services",
      "confidence": 0.450,
      "explanation": "Primary account for category 'Service'"
    },
    {
      "account": "3000 – Raw Materials",
      "confidence": 0.315,
      "explanation": "Alternative account for category 'Service'"
    },
    {
      "account": "4200 – Consumables",
      "confidence": 0.135,
      "explanation": "Fallback account for uncertain classification"
    }
  ],
  "semantic_category": "Service",
  "classification_confidence": 0.450,
  "classification_method": "llm",
  "classification_reasoning": "Custom manufacturing service based on technical drawing",
  "metadata": {
    "invoice_text": "Sonderanfertigung nach Zeichnung"
  }
}
```

---

## Batch Processing

### Example 6: Multiple Line Items

**Request:**
```json
POST /api/v1/suggest/batch
X-API-Key: your-api-key
Content-Type: application/json

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
    },
    {
      "invoice_text": "DeWalt Akkuschrauber 18V",
      "supplier": "ToolCenter AG",
      "unit_price": 289.00
    }
  ],
  "top_k": 2
}
```

**Response:**
```json
[
  {
    "suggestions": [
      {
        "account": "3000 – Raw Materials",
        "confidence": 0.920,
        "explanation": "Primary account for category 'Material' (Supplier: MetalWorks GmbH)"
      },
      {
        "account": "4200 – Consumables",
        "confidence": 0.644,
        "explanation": "Alternative account for category 'Material'"
      }
    ],
    "semantic_category": "Material",
    "classification_confidence": 0.920,
    "classification_method": "hybrid",
    "classification_reasoning": "Rule and LLM agree: Material-related keywords detected",
    "metadata": {
      "invoice_text": "Edelstahlrohr 12x1.5 mm",
      "supplier": "MetalWorks GmbH",
      "quantity": 50
    }
  },
  {
    "suggestions": [
      {
        "account": "4900 – Transport & Freight Costs",
        "confidence": 0.950,
        "explanation": "Primary account for category 'Transport'"
      },
      {
        "account": "4980 – Surcharges & Fees",
        "confidence": 0.665,
        "explanation": "Alternative account for category 'Transport'"
      }
    ],
    "semantic_category": "Transport",
    "classification_confidence": 0.950,
    "classification_method": "rule",
    "classification_reasoning": "Matched 2 keyword(s) for Transport",
    "metadata": {
      "invoice_text": "Transportkosten Lieferung",
      "line_amount": 150.00
    }
  },
  {
    "suggestions": [
      {
        "account": "6100 – Tools & Equipment",
        "confidence": 0.920,
        "explanation": "Primary account for category 'Tools' (Supplier: ToolCenter AG)"
      },
      {
        "account": "4200 – Consumables",
        "confidence": 0.276,
        "explanation": "Fallback account for uncertain classification"
      }
    ],
    "semantic_category": "Tools",
    "classification_confidence": 0.920,
    "classification_method": "rule",
    "classification_reasoning": "Matched 2 keyword(s) for Tools",
    "metadata": {
      "invoice_text": "DeWalt Akkuschrauber 18V",
      "supplier": "ToolCenter AG",
      "unit_price": 289.0
    }
  }
]
```

---

## Feedback Examples

### Example 7: Positive Feedback (Correct Suggestion)

**Request:**
```json
POST /api/v1/feedback
X-API-Key: your-api-key
Content-Type: application/json

{
  "invoice_text": "Edelstahlrohr 12x1.5 mm",
  "suggested_account": "3000 – Raw Materials",
  "actual_account": "3000 – Raw Materials",
  "user_id": "tenant_manufacturing_123",
  "comments": "Correct suggestion, approved without changes"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Feedback recorded successfully",
  "feedback_id": "fb_20260104_143052"
}
```

---

### Example 8: Corrective Feedback

**Request:**
```json
{
  "invoice_text": "Softwarelizenz CAD Tool",
  "suggested_account": "6000 – External Services",
  "actual_account": "6500 – IT & Software Expenses",
  "user_id": "tenant_engineering_456",
  "comments": "Should be IT expenses, not external services"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Feedback recorded successfully",
  "feedback_id": "fb_20260104_143125"
}
```

---

## Error Scenarios

### Example 9: Missing Required Field

**Request:**
```json
{
  "line_item": {
    "supplier": "Some Supplier"
  },
  "top_k": 3
}
```

**Response (400 Bad Request):**
```json
{
  "error": "ValidationError",
  "message": "Invalid request format",
  "details": {
    "field": "line_item.invoice_text",
    "issue": "Field required"
  }
}
```

---

### Example 10: Invalid API Key

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/suggest" \
  -H "X-API-Key: invalid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"line_item": {"invoice_text": "test"}}'
```

**Response (403 Forbidden):**
```json
{
  "error": "Forbidden",
  "message": "Invalid API Key"
}
```

---

### Example 11: Missing API Key

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/suggest" \
  -H "Content-Type: application/json" \
  -d '{"line_item": {"invoice_text": "test"}}'
```

**Response (401 Unauthorized):**
```json
{
  "error": "Unauthorized",
  "message": "API Key required"
}
```

---

### Example 12: Invalid top_k Value

**Request:**
```json
{
  "line_item": {
    "invoice_text": "Test item"
  },
  "top_k": 10
}
```

**Response (400 Bad Request):**
```json
{
  "error": "ValidationError",
  "message": "Invalid request format",
  "details": {
    "field": "top_k",
    "issue": "Value must be between 1 and 5"
  }
}
```

---

## Integration Examples

### Example 13: Python Integration

```python
import requests
from typing import List, Dict

class AccountCodingClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def suggest_account(self, invoice_text: str, **kwargs) -> Dict:
        """Get account suggestion for single line item."""
        payload = {
            "line_item": {
                "invoice_text": invoice_text,
                **kwargs
            },
            "top_k": 3
        }
        
        response = requests.post(
            f"{self.api_url}/api/v1/suggest",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def batch_suggest(self, line_items: List[Dict]) -> List[Dict]:
        """Get account suggestions for multiple items."""
        payload = {
            "line_items": line_items,
            "top_k": 3
        }
        
        response = requests.post(
            f"{self.api_url}/api/v1/suggest/batch",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = AccountCodingClient(
    api_url="https://account-coding-api.azurewebsites.net",
    api_key="your-api-key"
)

result = client.suggest_account(
    "Edelstahlrohr 12x1.5 mm",
    supplier="MetalWorks GmbH",
    quantity=50
)

print(f"Top account: {result['suggestions'][0]['account']}")
print(f"Confidence: {result['suggestions'][0]['confidence']}")
```

---

### Example 14: JavaScript/Node.js Integration

```javascript
const axios = require('axios');

class AccountCodingClient {
  constructor(apiUrl, apiKey) {
    this.apiUrl = apiUrl;
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }
  
  async suggestAccount(invoiceText, additionalData = {}) {
    const payload = {
      line_item: {
        invoice_text: invoiceText,
        ...additionalData
      },
      top_k: 3
    };
    
    const response = await axios.post(
      `${this.apiUrl}/api/v1/suggest`,
      payload,
      { headers: this.headers }
    );
    
    return response.data;
  }
  
  async batchSuggest(lineItems) {
    const payload = {
      line_items: lineItems,
      top_k: 3
    };
    
    const response = await axios.post(
      `${this.apiUrl}/api/v1/suggest/batch`,
      payload,
      { headers: this.headers }
    );
    
    return response.data;
  }
}

// Usage
const client = new AccountCodingClient(
  'https://account-coding-api.azurewebsites.net',
  'your-api-key'
);

client.suggestAccount('Edelstahlrohr 12x1.5 mm', {
  supplier: 'MetalWorks GmbH',
  quantity: 50
})
.then(result => {
  console.log('Top account:', result.suggestions[0].account);
  console.log('Confidence:', result.suggestions[0].confidence);
})
.catch(error => {
  console.error('Error:', error.message);
});
```

---

**Last Updated:** January 2026
