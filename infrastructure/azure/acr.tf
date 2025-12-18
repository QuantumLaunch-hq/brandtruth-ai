# infrastructure/azure/acr.tf
# Azure Container Registry for Docker images

resource "azurerm_container_registry" "main" {
  name                = "acr${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "Premium" : "Basic"
  admin_enabled       = true  # Enable for initial setup, disable later

  # Premium features (prod only)
  dynamic "georeplications" {
    for_each = var.environment == "prod" ? ["westus2"] : []
    content {
      location                = georeplications.value
      zone_redundancy_enabled = true
    }
  }

  tags = local.common_tags
}

# =============================================================================
# OUTPUTS FOR CI/CD
# =============================================================================

output "acr_login_server" {
  description = "ACR login server URL"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "ACR admin username"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "ACR admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}
