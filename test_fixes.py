from gl_predictor import GLPredictor

p = GLPredictor()
tests = [
    ('Werkzeugkoffer leer', '6100 – Tools & Equipment'),
    ('Beratungsleistung Engineering', '6000 – External Services'),
    ('Reparaturkosten Maschine Linie A', '6000 – External Services')
]

print('Testing targeted fixes for the 3 failure cases:\n')
for i, (text, expected) in enumerate(tests, 1):
    result = p.suggest(text, 1)[0]
    match = '✓' if result['account'] == expected else '✗'
    print(f'{i}. "{text}"')
    print(f'   Expected: {expected}')
    print(f'   Got:      {result["account"]} [{match}]')
    print(f'   Confidence: {result["confidence"]} | {result["explanation"]}\n')
