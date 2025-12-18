# infrastructure/azure/storage.tf
# Azure Blob Storage (replaces MinIO)

resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = var.environment == "prod" ? "GRS" : "LRS"
  account_kind             = "StorageV2"

  # Security settings
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = true  # Required for public ad creative URLs
  shared_access_key_enabled       = true

  blob_properties {
    versioning_enabled = var.environment == "prod"

    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "OPTIONS"]
      allowed_origins    = ["*"]  # Restrict in prod
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }

    delete_retention_policy {
      days = var.environment == "prod" ? 30 : 7
    }
  }

  tags = local.common_tags
}

# =============================================================================
# CONTAINERS (equivalent to MinIO buckets)
# =============================================================================

# Ad creatives storage (public read access)
resource "azurerm_storage_container" "ad_creatives" {
  name                  = "ad-creatives"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"  # Public read access for images
}

# Brand assets storage (public read access)
resource "azurerm_storage_container" "brand_assets" {
  name                  = "brand-assets"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "blob"
}

# Private storage for internal files
resource "azurerm_storage_container" "private" {
  name                  = "private"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Temporal workflow history (private)
resource "azurerm_storage_container" "temporal" {
  name                  = "temporal"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================================
# PRIVATE ENDPOINT (Production only)
# =============================================================================

resource "azurerm_private_endpoint" "storage" {
  count               = var.enable_private_endpoints ? 1 : 0
  name                = "pe-storage-${local.name_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.private_endpoints.id

  private_service_connection {
    name                           = "psc-storage"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "storage-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.blob[0].id]
  }

  tags = local.common_tags
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_primary_key" {
  description = "Storage account primary key"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "storage_account_connection_string" {
  description = "Storage account connection string"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "storage_blob_endpoint" {
  description = "Blob storage endpoint URL"
  value       = azurerm_storage_account.main.primary_blob_endpoint
}

output "ad_creatives_url" {
  description = "Ad creatives container URL"
  value       = "${azurerm_storage_account.main.primary_blob_endpoint}${azurerm_storage_container.ad_creatives.name}"
}
