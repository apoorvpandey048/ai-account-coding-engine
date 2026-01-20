# 🎯 Enable GitHub Pages (One-Time Setup)

## Steps to Activate Your Demo Page

1. **Go to your GitHub repository:**
   https://github.com/apoorvpandey048/ai-account-coding-engine

2. **Navigate to Settings → Pages** (left sidebar)

3. **Configure Source:**
   - Source: Deploy from a branch
   - Branch: `main`
   - Folder: `/ (root)`

4. **Click "Save"**

5. **Wait 1-2 minutes** for deployment

6. **Your demo will be live at:**
   https://apoorvpandey048.github.io/ai-account-coding-engine/

## 🎨 How to Use the Demo

### With Local Server (ngrok)

1. **Run the API locally:**
   ```powershell
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8005
   ```

2. **In another terminal, start ngrok:**
   ```powershell
   ngrok http 8005
   ```

3. **Copy the ngrok URL** (e.g., `https://abc123.ngrok-free.app`)

4. **Open your demo page:**
   https://apoorvpandey048.github.io/ai-account-coding-engine/

5. **Enter:**
   - API Host URL: `https://abc123.ngrok-free.app` (your ngrok URL)
   - API Key: `dev-key-001`

6. **Click any button** to test the endpoints!

### With Azure (When Available)

Simply enter your Azure App Service URL:
```
https://your-app.azurewebsites.net
```

## ✅ What You'll See

The demo page includes:
- ✨ Modern, responsive UI with gradient design
- 🎯 Interactive API testing buttons
- 📊 Real-time response display with syntax highlighting
- 🔧 Collapsible payload editors
- 💡 Status indicators (success/error badges)
- 📱 Mobile-friendly layout

## 🚀 Features Demonstrated

1. **Health Check** - Verify service is running
2. **GL Suggestion** - Get account recommendations for a single invoice line
3. **Batch Processing** - Process multiple lines at once
4. **Feedback** - Submit corrections for model improvement

## 🔒 Security Note

The demo key `dev-key-001` is for demonstration only. In production:
- Use secure, unique API keys per client
- Store keys in Azure Key Vault
- Enable rate limiting
- Use HTTPS only

## 📝 Next Steps

After the demo is live, share the link with your client:
```
https://apoorvpandey048.github.io/ai-account-coding-engine/
```

For local testing without Azure, follow the ngrok steps above.
