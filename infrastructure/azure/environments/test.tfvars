# infrastructure/azure/environments/test.tfvars
# Test environment configuration

environment = "test"
location    = "eastus2"

# =============================================================================
# DATABASE (cost-optimized for test)
# =============================================================================
postgres_sku        = "B_Standard_B1ms"  # Burstable, 1 vCore, 2GB RAM
postgres_storage_mb = 32768              # 32GB

# =============================================================================
# CONTAINER APPS (minimal for test)
# =============================================================================

# API
api_cpu          = 0.5
api_memory       = "1Gi"
api_min_replicas = 1
api_max_replicas = 2

# Frontend
frontend_cpu    = 0.25
frontend_memory = "0.5Gi"

# Worker
worker_cpu          = 0.5
worker_memory       = "1Gi"
worker_min_replicas = 1
worker_max_replicas = 2

# Temporal
temporal_cpu    = 0.5
temporal_memory = "1Gi"

# Qdrant
qdrant_cpu    = 0.25
qdrant_memory = "1Gi"

# =============================================================================
# SECURITY (relaxed for test)
# =============================================================================
enable_private_endpoints = false
enable_waf               = false
enable_monitoring        = true

# =============================================================================
# API KEYS (set via environment or terraform.tfvars.local)
# =============================================================================
# openai_api_key        = ""
# anthropic_api_key     = ""
# azure_openai_endpoint = ""
# azure_openai_api_key  = ""
# unsplash_access_key   = ""
# pexels_api_key        = ""
