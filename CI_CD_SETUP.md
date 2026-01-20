# CI/CD Setup Instructions

## Step 1: Get Azure Publish Profile

Run this command in Azure Cloud Shell (https://shell.azure.com):

```bash
az webapp deployment list-publishing-profiles \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding \
  --xml > publish-profile.xml

cat publish-profile.xml
```

Copy the entire XML output (from `<publishData>` to `</publishData>`).

## Step 2: Add Secret to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Value: Paste the XML content from Step 1
6. Click **Add secret**

## Step 3: Push Code to GitHub

```powershell
# From your local machine
cd c:\Users\Apoor\ai-account-coding-engine\ai-account-coding-engine

# Initialize git (if not already done)
git init
git add .
git commit -m "Add CI/CD pipeline and deployment updates"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to main branch (triggers deployment)
git push -u origin main
```

## Step 4: Monitor Deployment

1. Go to your GitHub repository
2. Click **Actions** tab
3. You'll see the workflow "Deploy to Azure App Service" running
4. Click on the workflow run to see logs

## Step 5: Verify Deployment

Once the workflow completes (green checkmark ✅):

```bash
# Test health endpoint
curl https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/health

# Test API with Pos
curl -X POST "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/suggest" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-001" \
  -d '{
    "line_item": {
      "invoice_text": "Rapido Drahtbinder",
      "pos": "10"
    },
    "top_k": 3
  }'
```

## Automatic Deployments

After setup, every push to `main` or `dev` branch will automatically:
1. Run tests
2. Build the application
3. Deploy to Azure App Service
4. Show deployment status in GitHub Actions

You can also trigger manual deployments:
- Go to **Actions** tab
- Select "Deploy to Azure App Service"
- Click **Run workflow** button
