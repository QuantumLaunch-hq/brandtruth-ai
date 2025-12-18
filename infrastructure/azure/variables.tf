# infrastructure/azure/variables.tf
# Input variables for BrandTruth AI infrastructure

# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "brandtruth"
}

variable "environment" {
  description = "Environment name (test, staging, prod)"
  type        = string
  validation {
    condition     = contains(["test", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: test, staging, prod"
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus2"
}

# =============================================================================
# CONTAINER IMAGES
# =============================================================================

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

variable "postgres_sku" {
  description = "PostgreSQL SKU name"
  type        = string
  default     = "B_Standard_B1ms"  # Burstable, 1 vCore, 2GB RAM - good for test
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768  # 32GB
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "brandtruth_admin"
}

# =============================================================================
# CONTAINER APP CONFIGURATION
# =============================================================================

variable "api_cpu" {
  description = "CPU cores for API container"
  type        = number
  default     = 0.5
}

variable "api_memory" {
  description = "Memory for API container (Gi)"
  type        = string
  default     = "1Gi"
}

variable "api_min_replicas" {
  description = "Minimum replicas for API"
  type        = number
  default     = 1
}

variable "api_max_replicas" {
  description = "Maximum replicas for API"
  type        = number
  default     = 3
}

variable "frontend_cpu" {
  description = "CPU cores for frontend container"
  type        = number
  default     = 0.25
}

variable "frontend_memory" {
  description = "Memory for frontend container (Gi)"
  type        = string
  default     = "0.5Gi"
}

variable "worker_cpu" {
  description = "CPU cores for worker container"
  type        = number
  default     = 1.0
}

variable "worker_memory" {
  description = "Memory for worker container (Gi)"
  type        = string
  default     = "2Gi"
}

variable "worker_min_replicas" {
  description = "Minimum replicas for worker"
  type        = number
  default     = 1
}

variable "worker_max_replicas" {
  description = "Maximum replicas for worker"
  type        = number
  default     = 5
}

variable "temporal_cpu" {
  description = "CPU cores for Temporal server"
  type        = number
  default     = 1.0
}

variable "temporal_memory" {
  description = "Memory for Temporal server (Gi)"
  type        = string
  default     = "2Gi"
}

variable "qdrant_cpu" {
  description = "CPU cores for Qdrant"
  type        = number
  default     = 0.5
}

variable "qdrant_memory" {
  description = "Memory for Qdrant (Gi)"
  type        = string
  default     = "2Gi"
}

# =============================================================================
# EXTERNAL API KEYS (Secrets)
# =============================================================================

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic (Claude) API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  default     = ""
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "unsplash_access_key" {
  description = "Unsplash API access key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "pexels_api_key" {
  description = "Pexels API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Ad Platform Credentials
variable "meta_access_token" {
  description = "Meta (Facebook) access token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "meta_ad_account_id" {
  description = "Meta ad account ID"
  type        = string
  default     = ""
}

variable "linkedin_access_token" {
  description = "LinkedIn access token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "linkedin_ad_account_id" {
  description = "LinkedIn ad account ID"
  type        = string
  default     = ""
}

# =============================================================================
# NETWORKING
# =============================================================================

variable "vnet_address_space" {
  description = "VNet address space"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "container_apps_subnet_prefix" {
  description = "Container Apps subnet prefix"
  type        = string
  default     = "10.0.0.0/23"  # /23 required for Container Apps
}

variable "database_subnet_prefix" {
  description = "Database subnet prefix"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_endpoints_subnet_prefix" {
  description = "Private endpoints subnet prefix"
  type        = string
  default     = "10.0.3.0/24"
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

variable "enable_private_endpoints" {
  description = "Enable private endpoints for PaaS services"
  type        = bool
  default     = false  # Set to true for prod
}

variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = false  # Set to true for prod
}

variable "enable_monitoring" {
  description = "Enable Azure Monitor and Log Analytics"
  type        = bool
  default     = true
}
