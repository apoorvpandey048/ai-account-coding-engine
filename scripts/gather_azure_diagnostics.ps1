param(
    [string]$subscriptionId = "3febb9fb-68b6-487d-a807-b5846d6cb419",
    [string]$resourceGroup = "ai-account-coding",
    [string]$webAppName = "ai-acc-coding-poc",
    [string]$assignee = "vincent.ochs@agalith.com"
)

$ts = Get-Date -Format yyyyMMdd-HHmmss
$dir = Join-Path -Path "diagnostics" -ChildPath $ts
New-Item -ItemType Directory -Force -Path $dir | Out-Null

Write-Host "Saving diagnostics to: $dir"

# Account and subscription
az account show --subscription $subscriptionId | Out-File -Encoding utf8 (Join-Path $dir 'account.json')

# Role assignments for the assignee and resource group
az role assignment list --assignee $assignee --all | Out-File -Encoding utf8 (Join-Path $dir 'role_assignments_assignee.json')
az role assignment list --scope "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup" | Out-File -Encoding utf8 (Join-Path $dir 'role_assignments_rg.json')

# Web App info
az webapp show --name $webAppName --resource-group $resourceGroup | Out-File -Encoding utf8 (Join-Path $dir 'webapp_show.json')

# Hostname and DNS
$web = az webapp show --name $webAppName --resource-group $resourceGroup --query "defaultHostName" -o tsv
if ($web) {
    Write-Host "Default host: $web"
    nslookup $web | Out-File -Encoding utf8 (Join-Path $dir 'nslookup.txt')
    try {
        Invoke-WebRequest -Uri "https://$web/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop | Out-File -Encoding utf8 (Join-Path $dir 'health_raw.txt')
    } catch {
        "Health check failed or not available: $($_.Exception.Message)" | Out-File -Encoding utf8 (Join-Path $dir 'health_raw.txt')
    }

    # Web App managed identity
    $identityJson = az webapp show --name $webAppName --resource-group $resourceGroup --query "identity" -o json
    if ($identityJson) {
        $identityJson | Out-File -Encoding utf8 (Join-Path $dir 'webapp_identity.json')
        try {
            $identity = $identityJson | ConvertFrom-Json
            if ($identity.principalId) {
                az role assignment list --assignee $identity.principalId --all | Out-File -Encoding utf8 (Join-Path $dir 'role_assignments_webapp_identity.json')
            }
        } catch {
            "Failed to parse webapp identity: $($_.Exception.Message)" | Out-File -Encoding utf8 (Join-Path $dir 'webapp_identity_error.txt')
        }
    }
}

# App settings and deployment source
az webapp config appsettings list --name $webAppName --resource-group $resourceGroup | Out-File -Encoding utf8 (Join-Path $dir 'appsettings.json')
az webapp deployment source show --name $webAppName --resource-group $resourceGroup | Out-File -Encoding utf8 (Join-Path $dir 'deployment_source.json')

# Publishing profile (sensitive) - save to file but mark as sensitive
az webapp deployment list-publishing-profiles --name $webAppName --resource-group $resourceGroup -o json > (Join-Path $dir 'publishing_profiles.json')

# Recent activity (deployments)
az webapp deployment source show --name $webAppName --resource-group $resourceGroup --query "repoUrl" -o tsv | Out-File -Encoding utf8 (Join-Path $dir 'repo_url.txt')

# List role assignments on key vaults referenced in appsettings (if any)
$settings = az webapp config appsettings list --name $webAppName --resource-group $resourceGroup -o json | ConvertFrom-Json
$kvname = $null
foreach ($s in $settings) {
    if ($s.name -like "*KEYVAULT*" -or $s.value -like "*vault.azure.net*") {
        $kvname = $s.value
        break
    }
}
if ($kvname) {
    "Key vault reference or URL found: $kvname" | Out-File -Encoding utf8 (Join-Path $dir 'keyvault_reference.txt')

    # Attempt to extract vault name from URL or value
    $vaultName = $null
    if ($kvname -match "https?://([^/.]+)\.vault\.azure\.net") {
        $vaultName = $Matches[1]
    } else {
        # fallback: assume the value might be the vault name
        $vaultName = $kvname -replace ".*/",""
    }

    if ($vaultName) {
        try {
            az keyvault show --name $vaultName --resource-group $resourceGroup | Out-File -Encoding utf8 (Join-Path $dir "keyvault_${vaultName}_show.json")
            az keyvault list --resource-group $resourceGroup | Out-File -Encoding utf8 (Join-Path $dir 'keyvaults_in_rg.json')
            az keyvault show --name $vaultName --query "properties.accessPolicies" -o json | Out-File -Encoding utf8 (Join-Path $dir "keyvault_${vaultName}_access_policies.json")

            # capture role assignments for the key vault resource
            $kv = az keyvault show --name $vaultName --resource-group $resourceGroup -o json | ConvertFrom-Json
            if ($kv.id) {
                az role assignment list --scope $kv.id --all | Out-File -Encoding utf8 (Join-Path $dir "role_assignments_keyvault_${vaultName}.json")
            }
        } catch {
            "Key Vault queries failed for $vaultName: $($_.Exception.Message)" | Out-File -Encoding utf8 (Join-Path $dir 'keyvault_error.txt')
        }
    }
}

Write-Host "Diagnostics collection complete. Files saved to $dir"
Write-Host "Tip: Commit the non-sensitive files in diagnostics to your repo or upload to a secure storage for sharing with the team."