# infrastructure/azure/database.tf
# Azure Database for PostgreSQL Flexible Server

# =============================================================================
# RANDOM PASSWORD FOR POSTGRES
# =============================================================================

resource "random_password" "postgres" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# =============================================================================
# POSTGRESQL FLEXIBLE SERVER
# =============================================================================

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-${local.name_prefix}-${random_string.suffix.result}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = var.postgres_version
  delegated_subnet_id    = azurerm_subnet.database.id
  private_dns_zone_id    = var.enable_private_endpoints ? azurerm_private_dns_zone.postgres[0].id : null

  administrator_login    = var.postgres_admin_username
  administrator_password = random_password.postgres.result

  sku_name   = var.postgres_sku
  storage_mb = var.postgres_storage_mb

  backup_retention_days        = var.environment == "prod" ? 35 : 7
  geo_redundant_backup_enabled = var.environment == "prod"

  zone = "1"

  high_availability {
    mode                      = var.environment == "prod" ? "ZoneRedundant" : "Disabled"
    standby_availability_zone = var.environment == "prod" ? "2" : null
  }

  maintenance_window {
    day_of_week  = 0  # Sunday
    start_hour   = 2
    start_minute = 0
  }

  tags = local.common_tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# =============================================================================
# DATABASES
# =============================================================================

resource "azurerm_postgresql_flexible_server_database" "brandtruth" {
  name      = "brandtruth"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_database" "temporal" {
  name      = "temporal"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_database" "temporal_visibility" {
  name      = "temporal_visibility"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "UUID-OSSP,PGCRYPTO,VECTOR"  # Enable vector extension for embeddings
}

resource "azurerm_postgresql_flexible_server_configuration" "max_connections" {
  name      = "max_connections"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = var.environment == "prod" ? "200" : "100"
}

# =============================================================================
# FIREWALL RULES (for public access during development)
# =============================================================================

# Allow Azure services (required for Container Apps)
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  count            = var.enable_private_endpoints ? 0 : 1
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "postgres_server_name" {
  description = "PostgreSQL server name"
  value       = azurerm_postgresql_flexible_server.main.name
}

output "postgres_server_fqdn" {
  description = "PostgreSQL server FQDN"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_admin_username" {
  description = "PostgreSQL admin username"
  value       = azurerm_postgresql_flexible_server.main.administrator_login
  sensitive   = true
}

output "postgres_admin_password" {
  description = "PostgreSQL admin password"
  value       = random_password.postgres.result
  sensitive   = true
}

output "postgres_connection_string" {
  description = "PostgreSQL connection string for brandtruth database"
  value       = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/brandtruth?sslmode=require"
  sensitive   = true
}

output "temporal_postgres_connection_string" {
  description = "PostgreSQL connection string for temporal database"
  value       = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${random_password.postgres.result}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/temporal?sslmode=require"
  sensitive   = true
}
