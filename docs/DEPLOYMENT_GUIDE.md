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
