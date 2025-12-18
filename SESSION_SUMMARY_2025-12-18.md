# Session Summary - December 18, 2025

## Context
Attempted to deploy BrandTruth AI to Azure Container Apps. Deployment failed with multiple issues. Decided to tear down and start fresh.

## Azure Resources Deleted
- Resource Group: `rg-quantumlaunch-test` (deletion in progress)
- All Container Apps, PostgreSQL, ACR, Storage, etc. will be removed

---

## Issues Found During Debugging

### 1. Temporal Server Failed to Start
**Problem:** Missing dynamic config file
```
Unable to create dynamic config client: config/dynamicconfig/development-sql.yaml: no such file or directory
```
**Fix Applied to Bicep:** Removed `DYNAMIC_CONFIG_FILE_PATH` env var (use Temporal defaults)
```bicep
// In infrastructure/azure/bicep/main.bicep, line ~172-179
// Removed: { name: 'DYNAMIC_CONFIG_FILE_PATH', value: 'config/dynamicconfig/development-sql.yaml' }
```

### 2. TEMPORAL_HOST Format Wrong
**Problem:** Code expects `host:port` format, but Bicep set them separately
```
API connecting to port 80 instead of 7233
tcp connect error: 100.100.249.50:80, Connection timed out
```
**Fix Applied to Bicep:** Changed to include port in TEMPORAL_HOST
```bicep
// Changed from:
{ name: 'TEMPORAL_HOST', value: 'ca-temporal-${environment}' }
{ name: 'TEMPORAL_PORT', value: '7233' }

// To:
{ name: 'TEMPORAL_HOST', value: 'ca-temporal-${environment}:7233' }
// Removed TEMPORAL_PORT
```

### 3. PostgreSQL Connection Exhaustion
**Problem:** B_Standard_B1ms SKU only has 50 max_connections, Temporal exhausts them
```
pq: remaining connection slots are reserved for roles with privileges of the "pg_use_reserved_connections" role
```
**Recommendation:** Use B_Standard_B2s or higher, OR configure Temporal with limited connection pool

### 4. Worker Image Stale
**Problem:** Deployed image missing `upload_image_to_meta_activity` function
```
ImportError: cannot import name 'upload_image_to_meta_activity' from 'src.temporal.activities.publish'
```
**Action Needed:** Rebuild and push worker image before next deployment

### 5. Frontend TypeScript Errors (Build Failures)
**Problems Found:**
- `image_matches?.matches?.find()` - Wrong type. `image_matches` is `Record<string, {...}>`, not array
- `result.brand_profile.tone_markers` - Property doesn't exist on BrandProfile type
- `mockVariants[index % mockVariants.length].image_url` - Could be undefined

**Fixes Applied by Linter** (already in codebase):
- `frontend/app/studio/page.tsx` - Fixed image_matches access pattern
- `frontend/app/dashboard/page.tsx` - Fixed image_matches access pattern

### 6. Frontend Running Dev Mode
**Problem:** Container was running `npm run dev` instead of production build
**Root Cause:** Dockerfile is correct (`CMD ["node", "server.js"]`), but image wasn't properly built

---

## Files Modified This Session

### Bicep Infrastructure (needs to be committed)
- `infrastructure/azure/bicep/main.bicep`
  - Removed DYNAMIC_CONFIG_FILE_PATH from Temporal
  - Changed TEMPORAL_HOST to include port for API and Worker

### Frontend TypeScript (fixed by linter, needs to be committed)
- `frontend/app/studio/page.tsx` - Fixed type errors
- `frontend/app/dashboard/page.tsx` - Fixed type errors

### CLAUDE.md Updated
- Added Docker development section
- Added Temporal workflow architecture
- Added database schema documentation
- Added environment variables section

---

## Pre-Deployment Checklist for Next Attempt

### 1. Fix and Test Frontend Build Locally
```bash
cd frontend
npm run build  # Must pass without errors
```

### 2. Test Full Stack Locally with Docker
```bash
docker-compose up -d
# Wait for all services to be healthy
# Test at http://localhost:3010
```

### 3. Verify Bicep Changes
```bash
cd infrastructure/azure/bicep
az bicep build --file main.bicep  # Should only show warnings, no errors
```

### 4. Create New Resource Group
```bash
az group create --name rg-quantumlaunch-test --location eastus2
```

### 5. Deploy Infrastructure
```bash
az deployment group create \
  --resource-group rg-quantumlaunch-test \
  --template-file main.bicep \
  --parameters parameters/test.bicepparam
```

### 6. Build and Push Images
```bash
# Login to ACR
az acr login --name <acr-name>

# Build for linux/amd64
docker build --platform linux/amd64 -t <acr>/quantumlaunch-api:v1 .
docker build --platform linux/amd64 -t <acr>/quantumlaunch-worker:v1 -f Dockerfile.worker .
docker build --platform linux/amd64 --build-arg NEXT_PUBLIC_API_URL=https://<api-fqdn> -t <acr>/quantumlaunch-frontend:v1 ./frontend

# Push all images
docker push <acr>/quantumlaunch-api:v1
docker push <acr>/quantumlaunch-worker:v1
docker push <acr>/quantumlaunch-frontend:v1
```

### 7. Update Container Apps with New Images
```bash
az containerapp update --name ca-api-test --resource-group rg-quantumlaunch-test --image <acr>/quantumlaunch-api:v1
az containerapp update --name ca-worker-test --resource-group rg-quantumlaunch-test --image <acr>/quantumlaunch-worker:v1
az containerapp update --name ca-frontend-test --resource-group rg-quantumlaunch-test --image <acr>/quantumlaunch-frontend:v1
```

---

## Architecture Reminder

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)         │  Studio, Campaigns, Dashboard         │
├─────────────────────────────────────────────────────────────────────────┤
│  API Server (FastAPI :8000)    │  /workflow/*, /api/campaigns/*        │
├─────────────────────────────────────────────────────────────────────────┤
│  Temporal Server (:7233)       │  Workflow orchestration (gRPC/TCP)    │
├─────────────────────────────────────────────────────────────────────────┤
│  Worker                        │  Executes pipeline activities          │
├─────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL                    │  App data + Temporal state             │
│  Qdrant (:6333)               │  Vector embeddings                      │
│  Azure Blob Storage            │  Ad creatives (replaces MinIO)         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Environment Variables for Azure Deployment

```bash
# API and Worker need:
DATABASE_URL=postgresql://<user>:<pass>@<host>:5432/quantumlaunch?sslmode=require
TEMPORAL_HOST=ca-temporal-test:7233  # MUST include port!
QDRANT_URL=http://ca-qdrant-test:6333
AZURE_STORAGE_ACCOUNT_NAME=<storage-account>
AZURE_STORAGE_BLOB_ENDPOINT=https://<storage-account>.blob.core.windows.net
ANTHROPIC_API_KEY=<from-keyvault>
PEXELS_API_KEY=<from-keyvault>

# Frontend needs (at BUILD time):
NEXT_PUBLIC_API_URL=https://ca-api-test.<env>.azurecontainerapps.io
DATABASE_URL=<same-as-above>  # For Prisma
```

---

## Commands to Resume

```bash
# Check if resource group deletion completed
az group show --name rg-quantumlaunch-test 2>&1
# Should return: "Resource group 'rg-quantumlaunch-test' could not be found"

# View current git status
cd /Users/satish/qlp-projects/adplatform
git status

# Commit the fixes before redeploying
git add infrastructure/azure/bicep/main.bicep frontend/app/studio/page.tsx frontend/app/dashboard/page.tsx CLAUDE.md
git commit -m "fix: Azure deployment issues - Temporal config, TypeScript errors"
```
