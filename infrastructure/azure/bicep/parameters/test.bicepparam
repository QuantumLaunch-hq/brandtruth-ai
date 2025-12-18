using '../main.bicep'

// Test Environment Parameters
// QuantumLaunch - A QuantumLayer Platform Company
// https://www.quantumlayerplatform.com/
//
// Deploy with:
//   az deployment group create \
//     --resource-group rg-quantumlaunch-test \
//     --template-file ../main.bicep \
//     --parameters test.bicepparam

param environment = 'test'
param location = 'eastus2'
param projectName = 'quantumlaunch'
param imageTag = 'latest'

// Database - Burstable (cost-optimized for test)
param postgresSku = 'B_Standard_B1ms'
param postgresStorageMb = 32768  // 32GB
param postgresAdminUsername = 'quantumlaunch_admin'

// Container App Resources - Minimal for test
param apiCpu = '0.5'
param apiMemory = '1Gi'
param apiMinReplicas = 1
param apiMaxReplicas = 2

param frontendCpu = '0.25'
param frontendMemory = '0.5Gi'

param workerCpu = '0.5'
param workerMemory = '1Gi'
param workerMinReplicas = 1
param workerMaxReplicas = 2

param temporalCpu = '0.5'
param temporalMemory = '1Gi'

param qdrantCpu = '0.25'
param qdrantMemory = '1Gi'
