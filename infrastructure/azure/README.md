# BrandTruth AI - Azure Infrastructure

Terraform configuration for deploying BrandTruth AI to Azure Container Apps.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Azure Resource Group                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Container Apps Environment                        │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │   API    │  │ Frontend │  │  Worker  │  │ Temporal │           │   │
│  │  │ (FastAPI)│  │ (Next.js)│  │          │  │  Server  │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  │                                                                     │   │
│  │  ┌──────────┐  ┌──────────┐                                        │   │
│  │  │  Qdrant  │  │ Temporal │                                        │   │
│  │  │ (Vector) │  │    UI    │                                        │   │
│  │  └──────────┘  └──────────┘                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                  │
│  │  PostgreSQL   │  │ Blob Storage  │  │   Key Vault   │                  │
│  │   Flexible    │  │  (ad assets)  │  │   (secrets)   │                  │
│  └───────────────┘  └───────────────┘  └───────────────┘                  │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐                                     │
│  │     ACR       │  │ Log Analytics │                                     │
│  │ (Docker imgs) │  │ (monitoring)  │                                     │
│  └───────────────┘  └───────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Azure CLI** installed and logged in
   ```bash
   az login
   az account set --subscription <subscription-id>
   ```

2. **Terraform** >= 1.5.0
   ```bash
   brew install terraform  # macOS
   ```

3. **Docker** for building images

## Quick Start

### 1. Initialize Terraform

```bash
cd infrastructure/azure
terraform init
```

### 2. Create secrets file (not committed to git)

```bash
cp environments/test.tfvars terraform.tfvars.local
```

Edit `terraform.tfvars.local` and add your API keys:
```hcl
openai_api_key        = "sk-..."
anthropic_api_key     = "sk-ant-..."
azure_openai_endpoint = "https://your-endpoint.openai.azure.com"
azure_openai_api_key  = "..."
unsplash_access_key   = "..."
pexels_api_key        = "..."
```

### 3. Plan and Apply

```bash
# Preview changes
terraform plan -var-file=environments/test.tfvars -var-file=terraform.tfvars.local

# Apply (creates all resources)
terraform apply -var-file=environments/test.tfvars -var-file=terraform.tfvars.local
```

### 4. Build and Push Docker Images

```bash
# Get ACR credentials
ACR_NAME=$(terraform output -raw acr_login_server)
ACR_USER=$(terraform output -raw acr_admin_username)
ACR_PASS=$(terraform output -raw acr_admin_password)

# Login to ACR
docker login $ACR_NAME -u $ACR_USER -p $ACR_PASS

# Build and push images
docker build -t $ACR_NAME/brandtruth-api:latest .
docker build -t $ACR_NAME/brandtruth-worker:latest -f Dockerfile.worker .
docker build -t $ACR_NAME/brandtruth-frontend:latest frontend/

docker push $ACR_NAME/brandtruth-api:latest
docker push $ACR_NAME/brandtruth-worker:latest
docker push $ACR_NAME/brandtruth-frontend:latest
```

### 5. Get URLs

```bash
terraform output urls
```

## Environments

| Environment | Config File | Description |
|-------------|-------------|-------------|
| test | `environments/test.tfvars` | Development/testing, minimal resources |
| staging | `environments/staging.tfvars` | Pre-production testing |
| prod | `environments/prod.tfvars` | Production, HA, private endpoints |

## Cost Estimates

### Test Environment (~$150/month)
- PostgreSQL B1ms: ~$25/month
- Container Apps: ~$50/month (minimal replicas)
- Storage: ~$5/month
- Other (Log Analytics, etc.): ~$70/month

### Production Environment (~$600-1000/month)
- PostgreSQL D2s_v3 with HA: ~$200/month
- Container Apps: ~$200-400/month (auto-scaling)
- Storage GRS: ~$20/month
- WAF, Private Endpoints: ~$100/month
- Other: ~$100/month

## Security

### Test Environment
- Public endpoints for easy access
- Firewall allows Azure services
- Basic monitoring

### Production Environment
- Private endpoints for all PaaS services
- VNet integration
- Key Vault for all secrets
- WAF protection
- Geo-redundant storage

## Troubleshooting

### View Container App logs
```bash
az containerapp logs show \
  --name ca-api-brandtruth-test \
  --resource-group rg-brandtruth-test \
  --follow
```

### Connect to PostgreSQL
```bash
# Get connection string
terraform output -raw postgres_connection_string

# Connect with psql (requires psql client)
psql "$(terraform output -raw postgres_connection_string)"
```

### Restart a Container App
```bash
az containerapp revision restart \
  --name ca-api-brandtruth-test \
  --resource-group rg-brandtruth-test
```

## Destroy Infrastructure

⚠️ **Warning**: This will delete all resources and data!

```bash
terraform destroy -var-file=environments/test.tfvars
```

## CI/CD

GitHub Actions workflow is configured in `.github/workflows/deploy.yml`.

Required GitHub Secrets:
- `AZURE_CREDENTIALS`: Service principal JSON
- `ACR_LOGIN_SERVER`: ACR URL (e.g., `acrbrandtruthtest123456.azurecr.io`)
- `ACR_USERNAME`: ACR admin username
- `ACR_PASSWORD`: ACR admin password
- `NEXT_PUBLIC_API_URL`: API URL for frontend

Create service principal:
```bash
az ad sp create-for-rbac \
  --name "github-actions-brandtruth" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-brandtruth-test \
  --sdk-auth
```
