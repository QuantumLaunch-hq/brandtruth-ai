// main.bicep
// QuantumLaunch - Azure Container Apps Infrastructure
// A QuantumLayer Platform Company (https://www.quantumlayerplatform.com/)
//
// Deploy with:
//   az deployment group create \
//     --resource-group rg-quantumlaunch-test \
//     --template-file main.bicep \
//     --parameters parameters/test.bicepparam

targetScope = 'resourceGroup'

// =============================================================================
// PARAMETERS
// =============================================================================

@description('Environment name (test, staging, prod)')
@allowed(['test', 'staging', 'prod'])
param environment string

@description('Azure region for resources')
param location string = resourceGroup().location

@description('Project name used in resource naming')
param projectName string = 'quantumlaunch'

@description('Docker image tag to deploy')
param imageTag string = 'latest'

// Database
@description('PostgreSQL SKU name')
param postgresSku string = 'B_Standard_B1ms'

@description('PostgreSQL storage in MB')
param postgresStorageMb int = 32768

@description('PostgreSQL admin username')
param postgresAdminUsername string = 'quantumlaunch_admin'

@secure()
@description('PostgreSQL admin password')
param postgresAdminPassword string = newGuid()

// Container App Resources
param apiCpu string = '0.5'
param apiMemory string = '1Gi'
param apiMinReplicas int = 1
param apiMaxReplicas int = 3

param frontendCpu string = '0.25'
param frontendMemory string = '0.5Gi'

param workerCpu string = '0.5'
param workerMemory string = '1Gi'
param workerMinReplicas int = 1
param workerMaxReplicas int = 3

param temporalCpu string = '0.5'
param temporalMemory string = '1Gi'

param qdrantCpu string = '0.25'
param qdrantMemory string = '1Gi'

// =============================================================================
// VARIABLES
// =============================================================================

var namePrefix = '${projectName}-${environment}'
var nameSuffix = uniqueString(resourceGroup().id)

var tags = {
  Project: projectName
  Environment: environment
  ManagedBy: 'Bicep'
}

// =============================================================================
// MODULES
// =============================================================================

// Log Analytics Workspace
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    name: 'log-${namePrefix}-${nameSuffix}'
    location: location
    tags: tags
    retentionDays: environment == 'prod' ? 90 : 30
  }
}

// Container Registry
module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    name: 'acr${projectName}${environment}${nameSuffix}'
    location: location
    tags: tags
    sku: environment == 'prod' ? 'Premium' : 'Basic'
  }
}

// Key Vault
module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    name: 'kv-${namePrefix}-${nameSuffix}'
    location: location
    tags: tags
  }
}

// Storage Account (replaces MinIO)
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    name: 'st${projectName}${environment}${nameSuffix}'
    location: location
    tags: tags
    sku: environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'
  }
}

// PostgreSQL Flexible Server
module database 'modules/database.bicep' = {
  name: 'database'
  params: {
    name: 'psql-${namePrefix}-${nameSuffix}'
    location: location
    tags: tags
    administratorLogin: postgresAdminUsername
    administratorPassword: postgresAdminPassword
    skuName: postgresSku
    storageSizeGB: postgresStorageMb / 1024
    highAvailability: environment == 'prod'
  }
}

// Container Apps Environment
module containerAppsEnv 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  params: {
    name: 'cae-${namePrefix}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
    logAnalyticsWorkspaceKey: logAnalytics.outputs.primaryKey
  }
}

// =============================================================================
// CONTAINER APPS
// =============================================================================

// Temporal Server (gRPC requires TCP transport)
module temporal 'modules/container-app.bicep' = {
  name: 'temporal'
  params: {
    name: 'ca-temporal-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: 'temporalio/auto-setup:1.24.2'
    containerPort: 7233
    cpu: temporalCpu
    memory: temporalMemory
    minReplicas: 1
    maxReplicas: 1
    external: false
    transport: 'tcp'  // CRITICAL: gRPC requires TCP transport
    healthProbeEnabled: false  // TCP doesn't support HTTP probes
    env: [
      { name: 'DB', value: 'postgresql' }
      { name: 'DB_PORT', value: '5432' }
      { name: 'POSTGRES_SEEDS', value: database.outputs.fqdn }
      { name: 'POSTGRES_USER', value: postgresAdminUsername }
      { name: 'POSTGRES_PWD', secretRef: 'postgres-password' }
      // Note: DYNAMIC_CONFIG_FILE_PATH removed - use Temporal defaults
      // The development-sql.yaml file doesn't exist in the container
    ]
    secrets: [
      { name: 'postgres-password', value: postgresAdminPassword }
    ]
  }
}

// Temporal UI
module temporalUi 'modules/container-app.bicep' = {
  name: 'temporal-ui'
  params: {
    name: 'ca-temporal-ui-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: 'temporalio/ui:2.26.2'
    containerPort: 8080
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: 1
    external: true
    env: [
      { name: 'TEMPORAL_ADDRESS', value: 'ca-temporal-${environment}:7233' }
      { name: 'TEMPORAL_CORS_ORIGINS', value: 'https://*' }
    ]
    secrets: []
  }
  dependsOn: [temporal]
}

// Qdrant Vector Database
module qdrant 'modules/container-app.bicep' = {
  name: 'qdrant'
  params: {
    name: 'ca-qdrant-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: 'qdrant/qdrant:v1.12.0'
    containerPort: 6333
    cpu: qdrantCpu
    memory: qdrantMemory
    minReplicas: 1
    maxReplicas: 1
    external: false
    env: [
      { name: 'QDRANT__LOG_LEVEL', value: 'INFO' }
    ]
    secrets: []
  }
}

// API (FastAPI)
module api 'modules/container-app.bicep' = {
  name: 'api'
  params: {
    name: 'ca-api-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: '${acr.outputs.loginServer}/quantumlaunch-api:${imageTag}'
    containerPort: 8000
    cpu: apiCpu
    memory: apiMemory
    minReplicas: apiMinReplicas
    maxReplicas: apiMaxReplicas
    external: true
    registryServer: acr.outputs.loginServer
    registryUsername: acr.outputs.adminUsername
    registryPassword: acr.outputs.adminPassword
    env: [
      { name: 'DATABASE_URL', value: 'postgresql://${postgresAdminUsername}:${postgresAdminPassword}@${database.outputs.fqdn}:5432/quantumlaunch?sslmode=require' }
      // TEMPORAL_HOST must include port - code expects format 'host:port'
      { name: 'TEMPORAL_HOST', value: 'ca-temporal-${environment}:7233' }
      { name: 'QDRANT_URL', value: 'http://ca-qdrant-${environment}:6333' }
      { name: 'AZURE_STORAGE_ACCOUNT_NAME', value: storage.outputs.name }
      { name: 'AZURE_STORAGE_BLOB_ENDPOINT', value: storage.outputs.blobEndpoint }
    ]
    secrets: [
      { name: 'storage-key', value: storage.outputs.primaryKey }
    ]
  }
  dependsOn: [temporal, qdrant, database]
}

// Worker (Temporal)
module worker 'modules/container-app.bicep' = {
  name: 'worker'
  params: {
    name: 'ca-worker-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: '${acr.outputs.loginServer}/quantumlaunch-worker:${imageTag}'
    containerPort: 8080 // Health check port if needed
    cpu: workerCpu
    memory: workerMemory
    minReplicas: workerMinReplicas
    maxReplicas: workerMaxReplicas
    external: false
    registryServer: acr.outputs.loginServer
    registryUsername: acr.outputs.adminUsername
    registryPassword: acr.outputs.adminPassword
    env: [
      { name: 'DATABASE_URL', value: 'postgresql://${postgresAdminUsername}:${postgresAdminPassword}@${database.outputs.fqdn}:5432/quantumlaunch?sslmode=require' }
      // TEMPORAL_HOST must include port - code expects format 'host:port'
      { name: 'TEMPORAL_HOST', value: 'ca-temporal-${environment}:7233' }
      { name: 'QDRANT_URL', value: 'http://ca-qdrant-${environment}:6333' }
      { name: 'AZURE_STORAGE_ACCOUNT_NAME', value: storage.outputs.name }
      { name: 'AZURE_STORAGE_BLOB_ENDPOINT', value: storage.outputs.blobEndpoint }
    ]
    secrets: [
      { name: 'storage-key', value: storage.outputs.primaryKey }
    ]
  }
  dependsOn: [temporal, qdrant, database]
}

// Frontend (Next.js) - Production build
module frontend 'modules/container-app.bicep' = {
  name: 'frontend'
  params: {
    name: 'ca-frontend-${environment}'
    location: location
    tags: tags
    containerAppsEnvironmentId: containerAppsEnv.outputs.id
    containerImage: '${acr.outputs.loginServer}/quantumlaunch-frontend:${imageTag}'
    containerPort: 3000
    cpu: frontendCpu
    memory: frontendMemory
    minReplicas: 1
    maxReplicas: 3
    external: true
    healthProbePath: '/api/health'  // Next.js API route for health
    registryServer: acr.outputs.loginServer
    registryUsername: acr.outputs.adminUsername
    registryPassword: acr.outputs.adminPassword
    env: [
      { name: 'DATABASE_URL', value: 'postgresql://${postgresAdminUsername}:${postgresAdminPassword}@${database.outputs.fqdn}:5432/quantumlaunch?sslmode=require' }
    ]
    secrets: []
  }
  dependsOn: [api]
}

// =============================================================================
// OUTPUTS
// =============================================================================

output acrLoginServer string = acr.outputs.loginServer
output apiUrl string = 'https://${api.outputs.fqdn}'
output frontendUrl string = 'https://${frontend.outputs.fqdn}'
output temporalUiUrl string = 'https://${temporalUi.outputs.fqdn}'
output keyVaultName string = keyVault.outputs.name
output storageAccountName string = storage.outputs.name
output databaseFqdn string = database.outputs.fqdn
