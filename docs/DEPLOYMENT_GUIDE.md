# Azure Deployment Guide

Step-by-step guide for deploying the AI Account Coding Service to Microsoft Azure.

## Deployment Options

1. **Azure App Service** - Recommended for quick deployment
2. **Azure Container Apps** - For containerized workloads
3. **Azure Kubernetes Service (AKS)** - For enterprise scale

This guide covers Options 1 and 2.

---

## Prerequisites

- Azure subscription
- Azure CLI installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
- Docker installed (for Container Apps)
- Azure OpenAI resource created

---

## Option 1: Azure App Service Deployment

### Step 1: Login to Azure

```bash
az login
az account set --subscription "Your Subscription Name"
```

### Step 2: Create Resource Group

```bash
az group create \
  --name rg-account-coding \
  --location westeurope
```

### Step 3: Create App Service Plan

```bash
az appservice plan create \
  --name plan-account-coding \
  --resource-group rg-account-coding \
  --sku B1 \
  --is-linux
```

**SKU Options:**
- `B1`: Basic ($13/month) - Development/testing
- `P1V2`: Premium ($100/month) - Production
- `P2V2`: Premium ($200/month) - High traffic

### Step 4: Create Web App

```bash
az webapp create \
  --resource-group rg-account-coding \
  --plan plan-account-coding \
  --name account-coding-api \
  --runtime "PYTHON:3.11"
```

**Note:** App name must be globally unique.

### Step 5: Configure Environment Variables

```bash
az webapp config appsettings set \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --settings \
    SERVICE_NAME="ai-account-coding-service" \
    ENVIRONMENT="production" \
    LOG_LEVEL="INFO" \
    API_KEY_REQUIRED="true" \
    VALID_API_KEYS="prod-key-001,prod-key-002" \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-azure-openai-key" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

### Step 6: Configure Startup Command

```bash
az webapp config set \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --startup-file "uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
```

### Step 7: Deploy Code

**Option A: Deploy from Local Git**

```bash
# Configure deployment user (one-time)
az webapp deployment user set \
  --user-name <username> \
  --password <password>

# Get Git URL
az webapp deployment source config-local-git \
  --name account-coding-api \
  --resource-group rg-account-coding

# Add Azure remote
git remote add azure <git-url-from-previous-command>

# Push code
git add .
git commit -m "Initial deployment"
git push azure main
```

**Option B: Deploy from GitHub**

```bash
az webapp deployment source config \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --repo-url https://github.com/your-repo \
  --branch main \
  --manual-integration
```

**Option C: Deploy ZIP**

```bash
# Create deployment package
zip -r deploy.zip . -x "*.git*" "*.env*" "venv/*" "__pycache__/*"

# Deploy
az webapp deployment source config-zip \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --src deploy.zip
```

### Step 8: Verify Deployment

```bash
# Check app status
az webapp show \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --query "state"

# Test health endpoint
curl https://account-coding-api.azurewebsites.net/health
```

### Step 9: View Logs

```bash
# Enable logging
az webapp log config \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --application-logging filesystem \
  --level information

# Stream logs
az webapp log tail \
  --name account-coding-api \
  --resource-group rg-account-coding
```

---

## Option 2: Azure Container Apps Deployment

### Step 1: Install Container Apps Extension

```bash
az extension add --name containerapp --upgrade
```

### Step 2: Register Providers

```bash
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

### Step 3: Create Container Registry (ACR)

```bash
az acr create \
  --resource-group rg-account-coding \
  --name accountcodingregistry \
  --sku Basic \
  --admin-enabled true
```

### Step 4: Build and Push Docker Image

```bash
# Login to ACR
az acr login --name accountcodingregistry

# Build image
docker build -t accountcodingregistry.azurecr.io/account-coding-api:v1 .

# Push image
docker push accountcodingregistry.azurecr.io/account-coding-api:v1
```

### Step 5: Create Container Apps Environment

```bash
az containerapp env create \
  --name env-account-coding \
  --resource-group rg-account-coding \
  --location westeurope
```

### Step 6: Deploy Container App

```bash
az containerapp create \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --environment env-account-coding \
  --image accountcodingregistry.azurecr.io/account-coding-api:v1 \
  --registry-server accountcodingregistry.azurecr.io \
  --registry-username accountcodingregistry \
  --registry-password <acr-password> \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    SERVICE_NAME="ai-account-coding-service" \
    ENVIRONMENT="production" \
    API_KEY_REQUIRED="true" \
    VALID_API_KEYS="prod-key-001" \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-key" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

### Step 7: Get App URL

```bash
az containerapp show \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --query properties.configuration.ingress.fqdn
```

---

## Security Configuration

### 1. Use Azure Key Vault for Secrets

```bash
# Create Key Vault
az keyvault create \
  --name kv-account-coding \
  --resource-group rg-account-coding \
  --location westeurope

# Add secrets
az keyvault secret set \
  --vault-name kv-account-coding \
  --name azure-openai-key \
  --value "your-azure-openai-key"

az keyvault secret set \
  --vault-name kv-account-coding \
  --name api-keys \
  --value "key1,key2,key3"
```

### 2. Enable Managed Identity

```bash
# For App Service
az webapp identity assign \
  --name account-coding-api \
  --resource-group rg-account-coding

# Grant Key Vault access
az keyvault set-policy \
  --name kv-account-coding \
  --object-id <managed-identity-principal-id> \
  --secret-permissions get list
```

### 3. Reference Secrets in App Settings

```bash
az webapp config appsettings set \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --settings \
    AZURE_OPENAI_API_KEY="@Microsoft.KeyVault(SecretUri=https://kv-account-coding.vault.azure.net/secrets/azure-openai-key/)"
```

---

## Monitoring and Diagnostics

### 1. Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app account-coding-insights \
  --location westeurope \
  --resource-group rg-account-coding

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app account-coding-insights \
  --resource-group rg-account-coding \
  --query instrumentationKey -o tsv)

# Configure App Service
az webapp config appsettings set \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

### 2. Set Up Alerts

```bash
# Alert for high error rate
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group rg-account-coding \
  --scopes /subscriptions/<sub-id>/resourceGroups/rg-account-coding/providers/Microsoft.Web/sites/account-coding-api \
  --condition "count requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action <action-group-id>
```

---

## Scaling Configuration

### App Service Scaling

```bash
# Auto-scale rules
az monitor autoscale create \
  --resource-group rg-account-coding \
  --resource account-coding-api \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-account-coding \
  --min-count 1 \
  --max-count 5 \
  --count 1

# Scale up on CPU > 70%
az monitor autoscale rule create \
  --resource-group rg-account-coding \
  --autoscale-name autoscale-account-coding \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

### Container Apps Scaling

```bash
# Update scaling rules
az containerapp update \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --min-replicas 2 \
  --max-replicas 10 \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50
```

---

## Custom Domain and SSL

### 1. Add Custom Domain

```bash
# Add domain
az webapp config hostname add \
  --webapp-name account-coding-api \
  --resource-group rg-account-coding \
  --hostname api.yourdomain.com

# Verify domain ownership (add TXT record to DNS)
az webapp config hostname list \
  --webapp-name account-coding-api \
  --resource-group rg-account-coding
```

### 2. Enable SSL

```bash
# Create managed certificate (free)
az webapp config ssl create \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --hostname api.yourdomain.com

# Or upload custom certificate
az webapp config ssl upload \
  --resource-group rg-account-coding \
  --name account-coding-api \
  --certificate-file path/to/cert.pfx \
  --certificate-password <password>
```

---

## Cost Optimization

### Estimated Monthly Costs

| Component | SKU | Cost (USD) |
|-----------|-----|------------|
| App Service (B1) | Basic | $13 |
| App Service (P1V2) | Premium | $100 |
| Azure OpenAI | GPT-4 | ~$3-30 (usage-based) |
| Application Insights | Standard | ~$2-10 |
| Storage (logs) | Standard | ~$1 |
| **Total (Basic)** | | **~$19-54/month** |
| **Total (Premium)** | | **~$106-141/month** |

### Cost Saving Tips

1. **Use B-series** for dev/test environments
2. **Auto-scale down** during off-hours
3. **Use deployment slots** to test before production
4. **Monitor Azure OpenAI usage** - implement caching for repeat requests
5. **Use reserved instances** for production (save up to 72%)

---

## Backup and Disaster Recovery

### 1. Configure Backups

```bash
# Create storage account for backups
az storage account create \
  --name accountcodingbackup \
  --resource-group rg-account-coding \
  --sku Standard_LRS

# Configure automated backups
az webapp config backup create \
  --resource-group rg-account-coding \
  --webapp-name account-coding-api \
  --container-url <storage-sas-url> \
  --backup-name daily-backup \
  --retention-period-in-days 30
```

### 2. Geo-Redundancy

Deploy to multiple regions:

```bash
# Primary: West Europe
# Secondary: North Europe

# Use Azure Traffic Manager or Front Door for load balancing
az network traffic-manager profile create \
  --name tm-account-coding \
  --resource-group rg-account-coding \
  --routing-method Performance
```

---

## Troubleshooting

### Check Deployment Status

```bash
az webapp deployment list-publishing-profiles \
  --name account-coding-api \
  --resource-group rg-account-coding
```

### Access Container Logs

```bash
# App Service
az webapp log download \
  --name account-coding-api \
  --resource-group rg-account-coding

# Container Apps
az containerapp logs show \
  --name account-coding-api \
  --resource-group rg-account-coding \
  --follow
```

### SSH into Container

```bash
# App Service
az webapp ssh \
  --name account-coding-api \
  --resource-group rg-account-coding
```

---

## Post-Deployment Checklist

- [ ] Health endpoint returns `200 OK`
- [ ] API key authentication works
- [ ] Azure OpenAI connection successful
- [ ] SSL certificate installed
- [ ] Application Insights collecting data
- [ ] Auto-scaling configured
- [ ] Alerts set up
- [ ] Backup configured
- [ ] Custom domain configured
- [ ] Documentation updated with production URLs

---

## Production Environment Variables

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
API_KEY_REQUIRED=true
VALID_API_KEYS=<secure-keys>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
APPLICATIONINSIGHTS_CONNECTION_STRING=<instrumentation-key>
```

---

## Support Resources

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Azure OpenAI**: https://learn.microsoft.com/azure/ai-services/openai/
- **App Service Docs**: https://docs.microsoft.com/azure/app-service/
- **Container Apps Docs**: https://docs.microsoft.com/azure/container-apps/

---

**Last Updated:** January 2026
---

## CI/CD Pipeline Setup

### GitHub Actions Workflow

Create `.github/workflows/deploy-azure.yml`:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main, dev]
  workflow_dispatch:

env:
  AZURE_WEBAPP_NAME: ai-acc-coding-poc
  PYTHON_VERSION: '3.11'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pip install pytest pytest-cov
        pytest tests/ --cov=src --cov-report=term
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        package: .
```

### Setting Up GitHub Secrets

```bash
# Get publish profile
az webapp deployment list-publishing-profiles \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding \
  --xml

# Add to GitHub Secrets:
# Repository Settings → Secrets and variables → Actions → New repository secret
# Name: AZURE_WEBAPP_PUBLISH_PROFILE
# Value: <paste XML content>
```

### Azure DevOps Pipeline

Create `azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
      - dev

pool:
  vmImage: 'ubuntu-latest'

variables:
  azureSubscription: 'ai-account-coding-connection'
  webAppName: 'ai-acc-coding-poc'
  pythonVersion: '3.11'

stages:
- stage: Build
  displayName: Build stage
  jobs:
  - job: BuildJob
    displayName: Build
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
      displayName: 'Install dependencies'
    
    - script: |
        pip install pytest pytest-cov
        pytest tests/ --cov=src --cov-report=xml --cov-report=html
      displayName: 'Run tests'
    
    - task: PublishTestResults@2
      inputs:
        testResultsFiles: '**/test-results.xml'
        testRunTitle: 'Python Tests'
    
    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: Cobertura
        summaryFileLocation: '$(System.DefaultWorkingDirectory)/**/coverage.xml'
    
    - task: ArchiveFiles@2
      inputs:
        rootFolderOrFile: '$(System.DefaultWorkingDirectory)'
        includeRootFolder: false
        archiveType: 'zip'
        archiveFile: '$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip'
      displayName: 'Archive files'
    
    - task: PublishBuildArtifacts@1
      inputs:
        PathtoPublish: '$(Build.ArtifactStagingDirectory)/$(Build.BuildId).zip'
        ArtifactName: 'drop'

- stage: Deploy
  displayName: Deploy stage
  dependsOn: Build
  condition: succeeded()
  jobs:
  - deployment: DeployWeb
    displayName: Deploy to Azure App Service
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebApp@1
            inputs:
              azureSubscription: '$(azureSubscription)'
              appType: 'webAppLinux'
              appName: '$(webAppName)'
              package: '$(Pipeline.Workspace)/drop/$(Build.BuildId).zip'
              runtimeStack: 'PYTHON|3.11'
              startUpCommand: 'uvicorn src.api.main:app --host 0.0.0.0 --port 8000'
```

---

## Current Azure App Service Configuration

Based on `resource-metadata.json`:

### Resource Details
- **Subscription ID:** `d56814fc-acb7-400b-8534-e44c3f850702`
- **Resource Group:** `ai-account-coding`
- **App Service Name:** `ai-acc-coding-poc`
- **Default Hostname:** `ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net`
- **Location:** `westeurope`
- **Managed Identity Principal ID:** `37f89824-cf61-40d2-b572-beb0da48d1b1`

### Configured App Settings

| Setting | Value | Description |
|---------|-------|-------------|
| `API_KEY_REQUIRED` | `true` | Enable API key authentication |
| `VALID_API_KEYS` | `dev-key-001` | Accepted API keys (comma-separated) |
| `AZURE_OPENAI_KEY` | `<secret>` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | `https://a-i-1.openai.azure.com` | Azure OpenAI endpoint |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` | API version |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4-1-mini` | Model deployment |
| `DATASET_BLOB_URL` | `https://aiacctcodingst01...` | Azure Blob Storage dataset URL |

### Storage Account
- **Name:** `aiacctcodingst01`
- **Container:** `datasets` (blob: `all_invoices_mapped.json`)
- **Static Website:** `https://aiacctcodingst01.z6.web.core.windows.net/`
- **RBAC Role:** Storage Blob Data Contributor assigned to App Service managed identity

### Key Vault
- **Name:** `aiacct-kv`
- **URI:** `https://aiacct-kv.vault.azure.net/`
- **Purpose:** Future secrets management (migration planned)

### CORS Configuration
- **Allowed Origins:** `https://aiacctcodingst01.z6.web.core.windows.net` (static website)
- **Allowed Methods:** `GET, POST, PUT, DELETE, OPTIONS`
- **Allowed Headers:** `*`

---

## Deployment Workflow

### 1. Manual Deployment (Current)

```bash
# From local machine
cd c:\Users\Apoor\ai-account-coding-engine\ai-account-coding-engine

# Login to Azure
az login

# Set subscription
az account set --subscription d56814fc-acb7-400b-8534-e44c3f850702

# Create deployment package
zip -r deploy.zip . -x "*.git*" ".env.example" "venv/*" "__pycache__/*" "deliverables/*" "_internal/*" "3_examples/*"

# Deploy to App Service
az webapp deployment source config-zip \
  --resource-group ai-account-coding \
  --name ai-acc-coding-poc \
  --src deploy.zip

# Restart app
az webapp restart \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding
```

### 2. Automated CI/CD (Recommended)

**Trigger:** Push to `main` or `dev` branch
**Steps:**
1. GitHub Actions detects push
2. Runs linters and tests
3. Builds deployment package (excludes `.git`, `deliverables/`, `_internal/`, test outputs)
4. Deploys to Azure App Service using publish profile
5. Restarts web app automatically
6. Sends deployment notification

**Setup:** Follow "CI/CD Pipeline Setup" section above

---

## Environment Variables Management

### Development (.env - committed to private repo)

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://a-i-1.openai.azure.com
AZURE_OPENAI_KEY=<real-key>
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-1-mini

# Azure Storage
STORAGE_ACCOUNT_NAME=aiacctcodingst01
STORAGE_ACCOUNT_KEY=<real-key>
DATASET_BLOB_URL=https://aiacctcodingst01.blob.core.windows.net/datasets/all_invoices_mapped.json

# API Configuration
API_KEY_REQUIRED=true
VALID_API_KEYS=dev-key-001
SERVICE_NAME=ai-account-coding-service
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

**Note:** `.env` is committed to repository (private repo - secrets safe). Used by:
- Local development (demo_local.py, testing)
- Azure OpenAI client initialization
- Storage access for dataset uploads

### Production (Azure App Service Settings)

Configured via:
```bash
az webapp config appsettings set \
  --resource-group ai-account-coding \
  --name ai-acc-coding-poc \
  --settings KEY=VALUE
```

Or via Azure Portal → App Service → Configuration → Application settings

**Recommendation:** Migrate secrets to Key Vault for production (see "Security Configuration" section)

---

## Post-Deployment Verification

### 1. Health Check

```bash
curl https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_openai_available": true
}
```

### 2. API Authentication Test

```bash
curl -X POST "https://ai-acc-coding-poc-fhg9e0bphrdab8b8.westeurope-01.azurewebsites.net/api/v1/suggest" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-001" \
  -d '{
    "line_item": {
      "invoice_text": "Test item",
      "pos": "10"
    },
    "top_k": 3
  }'
```

Expected: JSON response with suggestions array

### 3. Check Application Logs

```bash
az webapp log tail \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding
```

---

## Troubleshooting Deployment Issues

### Issue: "ModuleNotFoundError" after deployment

**Cause:** Missing dependencies in `requirements.txt`
**Fix:** Ensure all packages are listed, redeploy

### Issue: "502 Bad Gateway"

**Cause:** App startup failure (port mismatch, import errors)
**Fix:** Check logs, verify startup command:
```bash
az webapp config show \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding \
  --query "linuxFxVersion"
```

### Issue: "401 Unauthorized" for authenticated requests

**Cause:** App setting `VALID_API_KEYS` not synced
**Fix:** Verify app settings:
```bash
az webapp config appsettings list \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding \
  --query "[?name=='VALID_API_KEYS'].value"
```

### Issue: CORS errors in demo page

**Cause:** Static website origin not in allowed CORS origins
**Fix:** Add origin:
```bash
az webapp cors add \
  --name ai-acc-coding-poc \
  --resource-group ai-account-coding \
  --allowed-origins "https://aiacctcodingst01.z6.web.core.windows.net"
```

---

## Next Steps

1. **Set up CI/CD:** Configure GitHub Actions or Azure DevOps pipeline
2. **Migrate to Key Vault:** Move secrets from app settings to Key Vault
3. **Add monitoring:** Configure Application Insights dashboards and alerts
4. **Performance testing:** Load test with Apache Bench or Azure Load Testing
5. **Security hardening:** Enable Web Application Firewall (WAF), DDoS protection
6. **Documentation:** Update API_USAGE_GUIDE.md with production URLs