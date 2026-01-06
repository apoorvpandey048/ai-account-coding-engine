"""End-to-end integration tests for the FastAPI application."""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main_poc import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "predictor_loaded" in data
        assert "azure_openai_available" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestSuggestEndpoint:
    """Tests for /suggest endpoint."""
    
    def test_suggest_basic_request(self, client):
        """Test basic suggest request with minimal payload."""
        payload = {
            "text": "Edelstahlrohr 12x1.5 mm",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate response structure
        assert "text" in data
        assert "suggestions" in data
        assert "method" in data
        assert "debug" in data
        
        # Validate suggestions
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) <= 3
        
        for suggestion in data["suggestions"]:
            assert "account" in suggestion
            assert "confidence" in suggestion
            assert "explanation" in suggestion
            assert 0 <= suggestion["confidence"] <= 1
    
    def test_suggest_with_top_k_variations(self, client):
        """Test that top_k parameter controls number of suggestions."""
        for k in [1, 2, 3]:
            payload = {
                "text": "Transportkosten Lieferung",
                "top_k": k
            }
            response = client.post("/suggest", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["suggestions"]) <= k
    
    def test_suggest_transport_classification(self, client):
        """Test classification of transport-related item."""
        payload = {
            "text": "Transportkosten Lieferung Baustelle Zürich",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data["suggestions"]
        
        # Should classify as transport
        assert len(suggestions) > 0
        # The top suggestion should be transport-related
        assert "transport" in suggestions[0]["account"].lower() or "freight" in suggestions[0]["account"].lower()
    
    def test_suggest_consumables_classification(self, client):
        """Test classification of consumables."""
        payload = {
            "text": "Schrauben M6 Edelstahl 500St",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data["suggestions"]
        
        assert len(suggestions) > 0
        # Should classify as consumables
        assert "consumables" in suggestions[0]["account"].lower() or "4200" in suggestions[0]["account"]
    
    def test_suggest_tools_classification(self, client):
        """Test classification of tools."""
        payload = {
            "text": "DeWalt Bohrmaschine Professional",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data["suggestions"]
        
        assert len(suggestions) > 0
        # Should classify as tools
        assert "tools" in suggestions[0]["account"].lower() or "equipment" in suggestions[0]["account"].lower() or "6100" in suggestions[0]["account"]
    
    def test_suggest_missing_text(self, client):
        """Test that request without text field fails gracefully."""
        payload = {
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        # Should return validation error (422) or handle gracefully
        assert response.status_code in [400, 422, 500]
    
    def test_suggest_empty_text(self, client):
        """Test handling of empty text."""
        payload = {
            "text": "",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        # Should fail validation or return 500
        assert response.status_code in [400, 422, 500]
    
    def test_suggest_confidence_ordering(self, client):
        """Test that suggestions are ordered by confidence (descending)."""
        payload = {
            "text": "Edelstahlrohr 12x1.5 mm",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data["suggestions"]
        
        if len(suggestions) > 1:
            # Verify descending confidence order
            for i in range(len(suggestions) - 1):
                assert suggestions[i]["confidence"] >= suggestions[i + 1]["confidence"], \
                    "Suggestions should be ordered by confidence (descending)"
    
    def test_suggest_method_field(self, client):
        """Test that method field indicates classification approach."""
        payload = {
            "text": "Schrauben M6",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Method should be rule-based, ai, or hybrid
        assert data["method"] in ["rule-based", "ai", "hybrid", "none"]
    
    def test_suggest_debug_info(self, client):
        """Test that debug information is present."""
        payload = {
            "text": "Test item",
            "top_k": 3
        }
        response = client.post("/suggest", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        debug = data["debug"]
        
        assert "initial_confidence" in debug
        assert "final_confidence" in debug
        assert "ai_client_available" in debug


class TestFeedbackEndpoint:
    """Tests for /feedback endpoint."""
    
    def test_feedback_submission_success(self, client):
        """Test successful feedback submission."""
        payload = {
            "text": "Edelstahlrohr 12x1.5 mm",
            "selected_account": "3000 – Raw Materials",
            "confidence": 0.95,
            "notes": "Correct classification"
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "timestamp" in data
        assert data["text"] == payload["text"]
        assert data["selected_account"] == payload["selected_account"]
    
    def test_feedback_minimal_payload(self, client):
        """Test feedback with only required fields."""
        payload = {
            "text": "Test item",
            "selected_account": "4200 – Consumables"
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
    
    def test_feedback_missing_fields(self, client):
        """Test feedback with missing required fields."""
        payload = {
            "text": "Test item"
            # Missing selected_account
        }
        response = client.post("/feedback", json=payload)
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_feedback_persistence(self, client):
        """Test that feedback is persisted to file."""
        import os
        feedback_file = "data/feedback.jsonl"
        
        # Record initial file size/line count if exists
        initial_lines = 0
        if os.path.exists(feedback_file):
            with open(feedback_file, "r") as f:
                initial_lines = len(f.readlines())
        
        # Submit feedback
        payload = {
            "text": "Test persistence item",
            "selected_account": "4200 – Consumables",
            "notes": "Test"
        }
        response = client.post("/feedback", json=payload)
        assert response.status_code == 200
        
        # Verify file was updated
        if os.path.exists(feedback_file):
            with open(feedback_file, "r") as f:
                final_lines = len(f.readlines())
            assert final_lines > initial_lines, "Feedback should be appended to file"


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_complete_workflow(self, client):
        """Test complete workflow: suggest -> feedback."""
        # Step 1: Get suggestions
        suggest_payload = {
            "text": "Transportkosten Express",
            "top_k": 3
        }
        suggest_response = client.post("/suggest", json=suggest_payload)
        assert suggest_response.status_code == 200
        
        suggest_data = suggest_response.json()
        assert len(suggest_data["suggestions"]) > 0
        
        # Step 2: Submit feedback on top suggestion
        top_suggestion = suggest_data["suggestions"][0]
        feedback_payload = {
            "text": suggest_payload["text"],
            "selected_account": top_suggestion["account"],
            "confidence": top_suggestion["confidence"],
            "notes": "E2E test workflow"
        }
        feedback_response = client.post("/feedback", json=feedback_payload)
        assert feedback_response.status_code == 200
        
        feedback_data = feedback_response.json()
        assert "id" in feedback_data
    
    def test_multiple_classifications(self, client):
        """Test multiple different items are classified correctly."""
        test_cases = [
            ("Edelstahlrohr 12mm", ["material", "3000", "raw"]),
            ("Transportkosten", ["transport", "4900", "freight"]),
            ("Schrauben M6", ["consumables", "4200"]),
            ("Software Lizenz", ["software", "6500", "it"]),
            ("Wartungsservice", ["service", "6000", "external"]),
        ]
        
        for text, expected_keywords in test_cases:
            payload = {"text": text, "top_k": 3}
            response = client.post("/suggest", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            suggestions = data["suggestions"]
            assert len(suggestions) > 0
            
            # Check if at least one expected keyword appears in top suggestion
            top_account = suggestions[0]["account"].lower()
            found_match = any(keyword.lower() in top_account for keyword in expected_keywords)
            assert found_match, f"Expected keywords {expected_keywords} not found in '{top_account}' for '{text}'"


def run_all_integration_tests():
    """Run all integration tests without pytest."""
    print("=" * 70)
    print("Running API Integration Tests")
    print("=" * 70)
    print()
    
    # Create test client
    client = TestClient(app)
    
    # Track results
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Helper to run a test
    def run_test(test_name, test_func):
        nonlocal total_tests, passed_tests, failed_tests
        total_tests += 1
        try:
            test_func(client)
            passed_tests += 1
            print(f"✓ {test_name}")
        except AssertionError as e:
            failed_tests.append((test_name, str(e)))
            print(f"✗ {test_name}: {str(e)}")
        except Exception as e:
            failed_tests.append((test_name, f"Error: {str(e)}"))
            print(f"✗ {test_name}: Error: {str(e)}")
    
    # Health tests
    print("\n--- Health Endpoint Tests ---")
    health = TestHealthEndpoint()
    run_test("Health check", health.test_health_check)
    run_test("Root endpoint", health.test_root_endpoint)
    
    # Suggest tests
    print("\n--- Suggest Endpoint Tests ---")
    suggest = TestSuggestEndpoint()
    run_test("Basic suggest request", suggest.test_suggest_basic_request)
    run_test("Top-K variations", suggest.test_suggest_with_top_k_variations)
    run_test("Transport classification", suggest.test_suggest_transport_classification)
    run_test("Consumables classification", suggest.test_suggest_consumables_classification)
    run_test("Tools classification", suggest.test_suggest_tools_classification)
    run_test("Confidence ordering", suggest.test_suggest_confidence_ordering)
    run_test("Method field", suggest.test_suggest_method_field)
    run_test("Debug info", suggest.test_suggest_debug_info)
    
    # Feedback tests
    print("\n--- Feedback Endpoint Tests ---")
    feedback = TestFeedbackEndpoint()
    run_test("Feedback submission", feedback.test_feedback_submission_success)
    run_test("Minimal feedback payload", feedback.test_feedback_minimal_payload)
    
    # E2E tests
    print("\n--- End-to-End Workflow Tests ---")
    e2e = TestEndToEndWorkflow()
    run_test("Complete workflow", e2e.test_complete_workflow)
    run_test("Multiple classifications", e2e.test_multiple_classifications)
    
    # Summary
    print()
    print("=" * 70)
    print(f"Tests Complete: {passed_tests}/{total_tests} passed")
    if failed_tests:
        print(f"\nFailed tests ({len(failed_tests)}):")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
    else:
        print("\n✓ ALL TESTS PASSED")
    print("=" * 70)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
