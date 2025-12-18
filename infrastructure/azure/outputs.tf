# infrastructure/azure/outputs.tf
# All outputs for BrandTruth AI infrastructure

# =============================================================================
# RESOURCE GROUP
# =============================================================================

output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Resource group location"
  value       = azurerm_resource_group.main.location
}

# =============================================================================
# NETWORKING
# =============================================================================

output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Virtual Network name"
  value       = azurerm_virtual_network.main.name
}

# =============================================================================
# ALL URLS (for easy access)
# =============================================================================

output "urls" {
  description = "All service URLs"
  value = {
    api         = "https://${azurerm_container_app.api.ingress[0].fqdn}"
    frontend    = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
    temporal_ui = "https://${azurerm_container_app.temporal_ui.ingress[0].fqdn}"
    blob_storage = azurerm_storage_account.main.primary_blob_endpoint
  }
}

# =============================================================================
# CI/CD CONFIGURATION
# =============================================================================

output "cicd_config" {
  description = "Configuration values for CI/CD pipeline"
  value = {
    acr_login_server = azurerm_container_registry.main.login_server
    resource_group   = azurerm_resource_group.main.name
    api_app_name     = azurerm_container_app.api.name
    frontend_app_name = azurerm_container_app.frontend.name
    worker_app_name  = azurerm_container_app.worker.name
  }
}

output "cicd_secrets" {
  description = "Secrets needed for CI/CD (sensitive)"
  sensitive   = true
  value = {
    acr_username = azurerm_container_registry.main.admin_username
    acr_password = azurerm_container_registry.main.admin_password
  }
}
