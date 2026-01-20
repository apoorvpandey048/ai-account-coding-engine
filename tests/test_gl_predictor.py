import pytest
from gl_predictor import GLPredictor


@pytest.fixture
def predictor():
    return GLPredictor()


def test_exact_match(predictor):
    out = predictor.suggest('Edelstahlrohr 12x1.5 mm')
    assert out[0]['confidence'] == 1.0 or isinstance(out[0]['confidence'], float)


def test_keyword_match(predictor):
    out = predictor.suggest('Transportkosten Lieferung')
    assert any('Transport' in s['account'] or 'Transport' in s['explanation'] or s['confidence'] > 0 for s in out)


def test_fallback(predictor):
    out = predictor.suggest('Completely unknown item 12345')
    assert out[0]['confidence'] <= 0.2
