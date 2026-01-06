from src.api.main_poc import app
from fastapi.testclient import TestClient

with TestClient(app) as client:
    resp = client.post('/suggest', json={'text': 'Software Lizenz', 'top_k': 3})
    print('Status:', resp.status_code)
    print('Response:')
    import json
    print(json.dumps(resp.json(), indent=2))
