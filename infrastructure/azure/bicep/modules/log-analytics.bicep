// modules/log-analytics.bicep
// Log Analytics Workspace for Container Apps

param name string
param location string
param tags object
param retentionDays int = 30

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

output id string = logAnalytics.id
output name string = logAnalytics.name
output primaryKey string = logAnalytics.listKeys().primarySharedKey
