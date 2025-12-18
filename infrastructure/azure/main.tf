# infrastructure/azure/main.tf
# BrandTruth AI - Azure Container Apps Infrastructure
#
# Architecture:
#   - Container Apps Environment (shared)
#   - Container Apps: api, frontend, worker, temporal, temporal-ui, qdrant
#   - Azure Database for PostgreSQL Flexible Server
#   - Azure Blob Storage (replaces MinIO)
#   - Azure Container Registry
#   - Azure Key Vault for secrets
#   - VNet with private endpoints
#
# Usage:
#   terraform init
#   terraform plan -var-file=environments/test.tfvars
#   terraform apply -var-file=environments/test.tfvars

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
    azapi = {
      source  = "azure/azapi"
      version = "~> 1.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Remote state - uncomment and configure for team use
  # backend "azurerm" {
  #   resource_group_name  = "tfstate-rg"
  #   storage_account_name = "tfstatebrandtruth"
  #   container_name       = "tfstate"
  #   key                  = "brandtruth.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
      recover_soft_deleted_key_vaults = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

provider "azapi" {}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "azurerm_client_config" "current" {}

# =============================================================================
# RANDOM SUFFIX FOR UNIQUE NAMES
# =============================================================================

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# =============================================================================
# RESOURCE GROUP
# =============================================================================

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location

  tags = local.common_tags
}

# =============================================================================
# LOCAL VALUES
# =============================================================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedAt   = timestamp()
  }

  # Naming convention
  name_prefix = "${var.project_name}-${var.environment}"

  # Container image tags
  api_image      = "${azurerm_container_registry.main.login_server}/brandtruth-api:${var.image_tag}"
  frontend_image = "${azurerm_container_registry.main.login_server}/brandtruth-frontend:${var.image_tag}"
  worker_image   = "${azurerm_container_registry.main.login_server}/brandtruth-worker:${var.image_tag}"
}
