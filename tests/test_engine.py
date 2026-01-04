"""Unit tests for AI Account Coding Engine."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import AccountCodingEngine
from src.core.classifier import SemanticClassifier
from src.core.mapper import AccountMapper


def test_classifier_rule_based():
    """Test rule-based classification."""
    classifier = SemanticClassifier()
    
    # Test material classification
    result = classifier.classify("Edelstahlrohr 12x1.5 mm")
    assert result["category"] == "Material"
    assert result["confidence"] > 0.5
    assert result["method"] == "rule"
    print("✓ Rule-based material classification passed")
    
    # Test transport classification
    result = classifier.classify("Transportkosten Lieferung")
    assert result["category"] == "Transport"
    assert result["confidence"] > 0.5
    print("✓ Rule-based transport classification passed")
    
    # Test consumables classification
    result = classifier.classify("Schrauben M6 Edelstahl 500St")
    assert result["category"] == "Consumables"
    assert result["confidence"] > 0.5
    print("✓ Rule-based consumables classification passed")


def test_mapper():
    """Test account mapping."""
    mapper = AccountMapper()
    
    # Test material mapping
    suggestions = mapper.map_to_accounts(
        category="Material",
        classification_confidence=0.9,
        invoice_text="Test item",
        top_k=3
    )
    
    assert len(suggestions) > 0
    assert suggestions[0]["account"] == "3000 – Raw Materials"
    assert suggestions[0]["confidence"] == 0.9
    print("✓ Account mapping passed")
    
    # Test confidence reduction for alternatives
    assert suggestions[1]["confidence"] < suggestions[0]["confidence"]
    print("✓ Alternative account confidence reduction passed")


def test_engine_basic():
    """Test basic engine functionality without Azure OpenAI."""
    engine = AccountCodingEngine()
    
    # Test single suggestion
    result = engine.suggest_accounts(
        invoice_text="Edelstahlrohr 12x1.5 mm",
        supplier="MetalWorks GmbH"
    )
    
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0
    assert "semantic_category" in result
    assert "classification_confidence" in result
    assert result["semantic_category"] == "Material"
    print("✓ Basic engine suggestion passed")


def test_engine_batch():
    """Test batch processing."""
    engine = AccountCodingEngine()
    
    line_items = [
        {"invoice_text": "Edelstahlrohr 12x1.5 mm"},
        {"invoice_text": "Transportkosten Lieferung"},
        {"invoice_text": "Schrauben M6 500St"}
    ]
    
    results = engine.batch_suggest(line_items)
    
    assert len(results) == 3
    assert all("suggestions" in r for r in results)
    print("✓ Batch processing passed")


def test_all_categories():
    """Test classification of different categories."""
    classifier = SemanticClassifier()
    
    test_cases = [
        ("Edelstahlrohr 12mm", "Material"),
        ("Transportkosten", "Transport"),
        ("Schrauben", "Consumables"),
        ("Kleinmengenzuschlag", "Surcharge"),
        ("Softwarelizenz", "IT & Software"),
        ("DeWalt Bohrmaschine", "Tools"),
        ("Wartungsservice", "Service"),
        ("Schutzhelm", "Safety"),
        ("Maschinenöl", "Operating Supplies")
    ]
    
    for text, expected_category in test_cases:
        result = classifier.classify(text)
        assert result["category"] == expected_category, f"Failed for '{text}': expected {expected_category}, got {result['category']}"
        print(f"✓ Category '{expected_category}' classification passed")


def test_with_sample_data():
    """Test with actual sample data from CSV."""
    import pandas as pd
    
    engine = AccountCodingEngine()
    
    # Load sample data
    try:
        df = pd.read_csv('data/invoice_text_with_accounts.csv')
        
        # Test first 5 rows
        success_count = 0
        for idx, row in df.head(5).iterrows():
            result = engine.suggest_accounts(
                invoice_text=row['extracted_invoice_text']
            )
            
            # Check if result has required fields
            assert "suggestions" in result
            assert "semantic_category" in result
            assert len(result["suggestions"]) > 0
            
            success_count += 1
            print(f"✓ Sample data test {success_count}/5 passed: '{row['extracted_invoice_text'][:40]}...'")
        
        print(f"✓ All {success_count} sample data tests passed")
        
    except FileNotFoundError:
        print("⚠ Sample data file not found, skipping sample data tests")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running AI Account Coding Engine Tests")
    print("=" * 60)
    print()
    
    try:
        test_classifier_rule_based()
        print()
        
        test_mapper()
        print()
        
        test_engine_basic()
        print()
        
        test_engine_batch()
        print()
        
        test_all_categories()
        print()
        
        test_with_sample_data()
        print()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        raise
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ ERROR: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    run_all_tests()
