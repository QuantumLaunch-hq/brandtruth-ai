# infrastructure/azure/container-apps.tf
# Azure Container Apps for BrandTruth AI services

# =============================================================================
# LOG ANALYTICS WORKSPACE
# =============================================================================

resource "azurerm_log_analytics_workspace" "main" {
  count               = var.enable_monitoring ? 1 : 0
  name                = "log-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APPS ENVIRONMENT
# =============================================================================

resource "azurerm_container_app_environment" "main" {
  name                       = "cae-${local.name_prefix}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = var.enable_monitoring ? azurerm_log_analytics_workspace.main[0].id : null

  infrastructure_subnet_id = azurerm_subnet.container_apps.id

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APP: API (FastAPI Backend)
# =============================================================================

resource "azurerm_container_app" "api" {
  name                         = "ca-api-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "api"
      image  = local.api_image
      cpu    = var.api_cpu
      memory = var.api_memory

      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.main.name
      }

      env {
        name        = "AZURE_STORAGE_ACCOUNT_KEY"
        secret_name = "storage-account-key"
      }

      env {
        name  = "AZURE_STORAGE_BLOB_ENDPOINT"
        value = azurerm_storage_account.main.primary_blob_endpoint
      }

      env {
        name  = "TEMPORAL_HOST"
        value = "ca-temporal-${local.name_prefix}"
      }

      env {
        name  = "TEMPORAL_PORT"
        value = "7233"
      }

      env {
        name  = "QDRANT_URL"
        value = "http://ca-qdrant-${local.name_prefix}:6333"
      }

      # API Keys from Key Vault
      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = var.azure_openai_endpoint
      }

      env {
        name        = "UNSPLASH_ACCESS_KEY"
        secret_name = "unsplash-access-key"
      }

      env {
        name        = "PEXELS_API_KEY"
        secret_name = "pexels-api-key"
      }

      # Health probe
      liveness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
      }

      readiness_probe {
        transport = "HTTP"
        path      = "/health"
        port      = 8000
      }
    }

    min_replicas = var.api_min_replicas
    max_replicas = var.api_max_replicas
  }

  # Secrets (referenced from Key Vault or directly)
  secret {
    name  = "database-url"
    value = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/brandtruth?sslmode=require"
  }

  secret {
    name  = "storage-account-key"
    value = azurerm_storage_account.main.primary_access_key
  }

  secret {
    name  = "anthropic-api-key"
    value = var.anthropic_api_key != "" ? var.anthropic_api_key : "not-configured"
  }

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key != "" ? var.openai_api_key : "not-configured"
  }

  secret {
    name  = "azure-openai-api-key"
    value = var.azure_openai_api_key != "" ? var.azure_openai_api_key : "not-configured"
  }

  secret {
    name  = "unsplash-access-key"
    value = var.unsplash_access_key != "" ? var.unsplash_access_key : "not-configured"
  }

  secret {
    name  = "pexels-api-key"
    value = var.pexels_api_key != "" ? var.pexels_api_key : "not-configured"
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APP: FRONTEND (Next.js)
# =============================================================================

resource "azurerm_container_app" "frontend" {
  name                         = "ca-frontend-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "frontend"
      image  = local.frontend_image
      cpu    = var.frontend_cpu
      memory = var.frontend_memory

      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = "https://${azurerm_container_app.api.ingress[0].fqdn}"
      }

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }

      env {
        name  = "NEXTAUTH_URL"
        value = "https://ca-frontend-${local.name_prefix}.${azurerm_container_app_environment.main.default_domain}"
      }

      env {
        name        = "NEXTAUTH_SECRET"
        secret_name = "nextauth-secret"
      }
    }

    min_replicas = 1
    max_replicas = 3
  }

  secret {
    name  = "database-url"
    value = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/brandtruth?sslmode=require"
  }

  secret {
    name  = "nextauth-secret"
    value = random_password.nextauth_secret.result
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  tags = local.common_tags
}

resource "random_password" "nextauth_secret" {
  length  = 32
  special = false
}

# =============================================================================
# CONTAINER APP: WORKER (Temporal Worker)
# =============================================================================

resource "azurerm_container_app" "worker" {
  name                         = "ca-worker-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "worker"
      image  = local.worker_image
      cpu    = var.worker_cpu
      memory = var.worker_memory

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }

      env {
        name  = "TEMPORAL_HOST"
        value = "ca-temporal-${local.name_prefix}"
      }

      env {
        name  = "TEMPORAL_PORT"
        value = "7233"
      }

      env {
        name  = "AZURE_STORAGE_ACCOUNT_NAME"
        value = azurerm_storage_account.main.name
      }

      env {
        name        = "AZURE_STORAGE_ACCOUNT_KEY"
        secret_name = "storage-account-key"
      }

      env {
        name  = "QDRANT_URL"
        value = "http://ca-qdrant-${local.name_prefix}:6333"
      }

      # AI API Keys
      env {
        name        = "ANTHROPIC_API_KEY"
        secret_name = "anthropic-api-key"
      }

      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }

      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = var.azure_openai_endpoint
      }

      env {
        name        = "UNSPLASH_ACCESS_KEY"
        secret_name = "unsplash-access-key"
      }

      env {
        name        = "PEXELS_API_KEY"
        secret_name = "pexels-api-key"
      }
    }

    min_replicas = var.worker_min_replicas
    max_replicas = var.worker_max_replicas
  }

  secret {
    name  = "database-url"
    value = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/brandtruth?sslmode=require"
  }

  secret {
    name  = "storage-account-key"
    value = azurerm_storage_account.main.primary_access_key
  }

  secret {
    name  = "anthropic-api-key"
    value = var.anthropic_api_key != "" ? var.anthropic_api_key : "not-configured"
  }

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key != "" ? var.openai_api_key : "not-configured"
  }

  secret {
    name  = "azure-openai-api-key"
    value = var.azure_openai_api_key != "" ? var.azure_openai_api_key : "not-configured"
  }

  secret {
    name  = "unsplash-access-key"
    value = var.unsplash_access_key != "" ? var.unsplash_access_key : "not-configured"
  }

  secret {
    name  = "pexels-api-key"
    value = var.pexels_api_key != "" ? var.pexels_api_key : "not-configured"
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APP: TEMPORAL SERVER
# =============================================================================

resource "azurerm_container_app" "temporal" {
  name                         = "ca-temporal-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "temporal"
      image  = "temporalio/auto-setup:1.22.4"
      cpu    = var.temporal_cpu
      memory = var.temporal_memory

      env {
        name  = "DB"
        value = "postgresql"
      }

      env {
        name  = "DB_PORT"
        value = "5432"
      }

      env {
        name  = "POSTGRES_HOST"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }

      env {
        name  = "POSTGRES_USER"
        value = azurerm_postgresql_flexible_server.main.administrator_login
      }

      env {
        name        = "POSTGRES_PWD"
        secret_name = "postgres-password"
      }

      env {
        name  = "POSTGRES_SEEDS"
        value = azurerm_postgresql_flexible_server.main.fqdn
      }

      env {
        name  = "DYNAMIC_CONFIG_FILE_PATH"
        value = "config/dynamicconfig/development-sql.yaml"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  secret {
    name  = "postgres-password"
    value = random_password.postgres.result
  }

  ingress {
    external_enabled = false  # Internal only
    target_port      = 7233
    transport        = "tcp"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APP: TEMPORAL UI
# =============================================================================

resource "azurerm_container_app" "temporal_ui" {
  name                         = "ca-temporal-ui-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "temporal-ui"
      image  = "temporalio/ui:2.21.3"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "TEMPORAL_ADDRESS"
        value = "ca-temporal-${local.name_prefix}:7233"
      }

      env {
        name  = "TEMPORAL_CORS_ORIGINS"
        value = "http://localhost:3000"
      }
    }

    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags
}

# =============================================================================
# CONTAINER APP: QDRANT (Vector Database)
# =============================================================================

resource "azurerm_container_app" "qdrant" {
  name                         = "ca-qdrant-${local.name_prefix}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "qdrant"
      image  = "qdrant/qdrant:v1.12.0"
      cpu    = var.qdrant_cpu
      memory = var.qdrant_memory

      env {
        name  = "QDRANT__LOG_LEVEL"
        value = "INFO"
      }

      # Volume mount for persistence would go here
      # Azure Container Apps supports Azure Files for persistent storage
    }

    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    external_enabled = false  # Internal only
    target_port      = 6333
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = local.common_tags
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "api_url" {
  description = "API URL"
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}"
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
}

output "temporal_ui_url" {
  description = "Temporal UI URL"
  value       = "https://${azurerm_container_app.temporal_ui.ingress[0].fqdn}"
}

output "container_apps_environment_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.main.id
}
