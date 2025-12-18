// modules/database.bicep
// Azure PostgreSQL Flexible Server

param name string
param location string
param tags object

param administratorLogin string
@secure()
param administratorPassword string

param skuName string = 'B_Standard_B1ms'
param storageSizeGB int = 32
param highAvailability bool = false

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: contains(skuName, 'B_') ? 'Burstable' : contains(skuName, 'GP_') ? 'GeneralPurpose' : 'MemoryOptimized'
  }
  properties: {
    version: '16'
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    storage: {
      storageSizeGB: storageSizeGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: highAvailability ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: highAvailability ? 'ZoneRedundant' : 'Disabled'
    }
  }
}

// Firewall rule to allow Azure services
resource firewallAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Firewall rule to allow all (for test only, restrict in prod)
resource firewallAllowAll 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgres
  name: 'AllowAll'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '255.255.255.255'
  }
}

// Create databases
resource quantumlaunchDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: 'quantumlaunch'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource temporalDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: 'temporal'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource temporalVisibilityDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: 'temporal_visibility'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

output id string = postgres.id
output name string = postgres.name
output fqdn string = postgres.properties.fullyQualifiedDomainName
