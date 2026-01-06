"""Quick test to verify Azure OpenAI settings load correctly."""
from src.utils.config import get_settings

settings = get_settings()

print("=" * 60)
print("CONFIGURATION TEST")
print("=" * 60)
print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
print(f"API Key: {'SET (' + settings.AZURE_OPENAI_KEY[:20] + '...' + ')' if settings.AZURE_OPENAI_KEY else 'MISSING'}")
print(f"API Version: {settings.AZURE_OPENAI_API_VERSION}")
print(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
print(f"Model: {settings.AZURE_OPENAI_MODEL}")
print(f"Temperature: {settings.AZURE_OPENAI_TEMPERATURE}")
print(f"Max Output Tokens: {settings.AZURE_OPENAI_MAX_OUTPUT_TOKENS}")
print("=" * 60)

if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY:
    print("[OK] Azure OpenAI configuration loaded successfully!")
else:
    print("[ERROR] Missing required Azure OpenAI configuration")
