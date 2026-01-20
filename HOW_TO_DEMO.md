# How to Demo the API (Azure App Service Unavailable)

Since the Azure App Service quota is exceeded, follow these steps to demo the API locally with GitHub Pages:

## Step 1: Start the API Locally

```powershell
# Navigate to project directory
cd ai-account-coding-engine

# Start the FastAPI server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8005
```

You should see: "Account Coding Engine initialized successfully"

## Step 2: Expose via Ngrok

Install ngrok from https://ngrok.com/download, then:

```powershell
# In a NEW terminal
ngrok http 8005
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

## Step 3: Use the GitHub Pages Demo

1. Open: https://apoorvpandey048.github.io/ai-account-coding-engine/
2. Paste your ngrok URL in "API Host URL"
3. Enter API key: `dev-key-001`
4. Click any button to test

## Endpoints Available

- **Health Check**: Verify service status
- **Get GL Suggestion**: Get account recommendation for single invoice line
- **Batch Process**: Process multiple lines at once
- **Send Feedback**: Submit corrections

## Troubleshooting

### "Network Error"
- Verify uvicorn is running (check terminal output)
- Verify ngrok tunnel is active
- Use the **HTTPS** URL from ngrok (not localhost)
- Check API key is exactly: `dev-key-001`

### CORS Errors
- The FastAPI app should have CORS enabled (check src/api/main.py)
- Ngrok should work without CORS issues

### Azure Status
Azure App Service `ai-acc-coding-poc` is currently unavailable due to Free tier quota exceeded. Options:
1. Continue with local + ngrok demo (no cost)
2. Wait for quota reset (monthly)
3. Upgrade to Basic B1 tier (~$13/month) with client approval

## Example Test

After setup, test the health endpoint:
- Click "Health Check" button
- You should see: `{"service":"AI Account Coding Service","version":"1.0.0","status":"running"}`

## For Client Presentation

1. Open two terminals (API + ngrok)
2. Open the GitHub Pages demo in browser
3. Show live API calls with immediate responses
4. Demonstrate all 4 endpoints
5. Explain that the production deployment will use Azure (once quota/upgrade resolved)
