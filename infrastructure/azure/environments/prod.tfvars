# infrastructure/azure/environments/prod.tfvars
# Production environment configuration

environment = "prod"
location    = "eastus2"

# =============================================================================
# DATABASE (production-grade)
# =============================================================================
postgres_sku        = "GP_Standard_D2s_v3"  # General Purpose, 2 vCores, 8GB RAM
postgres_storage_mb = 131072                 # 128GB

# =============================================================================
# CONTAINER APPS (production scale)
# =============================================================================

# API
api_cpu          = 1.0
api_memory       = "2Gi"
api_min_replicas = 2
api_max_replicas = 10

# Frontend
frontend_cpu    = 0.5
frontend_memory = "1Gi"

# Worker (needs more resources for AI workloads)
worker_cpu          = 2.0
worker_memory       = "4Gi"
worker_min_replicas = 2
worker_max_replicas = 10

# Temporal
temporal_cpu    = 1.0
temporal_memory = "2Gi"

# Qdrant
qdrant_cpu    = 1.0
qdrant_memory = "4Gi"

# =============================================================================
# SECURITY (hardened for prod)
# =============================================================================
enable_private_endpoints = true
enable_waf               = true
enable_monitoring        = true

# =============================================================================
# API KEYS (set via environment or terraform.tfvars.local)
# =============================================================================
# These should be set via:
# - Azure DevOps variable groups
# - GitHub Actions secrets
# - terraform.tfvars.local (not committed)
#
# openai_api_key        = ""
# anthropic_api_key     = ""
# azure_openai_endpoint = ""
# azure_openai_api_key  = ""
# unsplash_access_key   = ""
# pexels_api_key        = ""
