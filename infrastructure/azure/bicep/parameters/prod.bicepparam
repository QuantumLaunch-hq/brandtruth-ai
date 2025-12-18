using '../main.bicep'

// Production Environment Parameters
// QuantumLaunch - A QuantumLayer Platform Company
// https://www.quantumlayerplatform.com/
//
// Deploy with:
//   az deployment group create \
//     --resource-group rg-quantumlaunch-prod \
//     --template-file ../main.bicep \
//     --parameters prod.bicepparam

param environment = 'prod'
param location = 'eastus2'
param projectName = 'quantumlaunch'
param imageTag = 'latest'

// Database - General Purpose (production performance)
param postgresSku = 'GP_Standard_D2s_v3'
param postgresStorageMb = 131072  // 128GB
param postgresAdminUsername = 'quantumlaunch_admin'

// Container App Resources - Production capacity
param apiCpu = '1'
param apiMemory = '2Gi'
param apiMinReplicas = 2
param apiMaxReplicas = 10

param frontendCpu = '0.5'
param frontendMemory = '1Gi'

param workerCpu = '1'
param workerMemory = '2Gi'
param workerMinReplicas = 2
param workerMaxReplicas = 10

param temporalCpu = '1'
param temporalMemory = '2Gi'

param qdrantCpu = '0.5'
param qdrantMemory = '2Gi'
