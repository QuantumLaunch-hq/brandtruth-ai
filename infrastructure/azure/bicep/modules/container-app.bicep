// modules/container-app.bicep
// Reusable Azure Container App with production-ready configuration

param name string
param location string
param tags object

param containerAppsEnvironmentId string
param containerImage string
param containerPort int = 8080

param cpu string = '0.5'
param memory string = '1Gi'
param minReplicas int = 0
param maxReplicas int = 3

param external bool = false

// Transport: 'auto', 'http', 'http2', 'tcp' (use 'tcp' for gRPC like Temporal)
@allowed(['auto', 'http', 'http2', 'tcp'])
param transport string = 'auto'

param registryServer string = ''
param registryUsername string = ''
@secure()
param registryPassword string = ''

param env array = []
param secrets array = []

// Health probe configuration
param healthProbePath string = '/health'
param healthProbeEnabled bool = true

var registrySecrets = !empty(registryServer) ? [
  {
    name: 'registry-password'
    value: registryPassword
  }
] : []

var allSecrets = concat(registrySecrets, secrets)

var registryConfig = !empty(registryServer) ? [
  {
    server: registryServer
    username: registryUsername
    passwordSecretRef: 'registry-password'
  }
] : []

// Health probes - only for HTTP/HTTP2 transport (not TCP)
var healthProbes = (healthProbeEnabled && transport != 'tcp') ? [
  {
    type: 'Startup'
    httpGet: {
      path: healthProbePath
      port: containerPort
      scheme: 'HTTP'
    }
    initialDelaySeconds: 10
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 30
    successThreshold: 1
  }
  {
    type: 'Liveness'
    httpGet: {
      path: healthProbePath
      port: containerPort
      scheme: 'HTTP'
    }
    initialDelaySeconds: 30
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  }
  {
    type: 'Readiness'
    httpGet: {
      path: healthProbePath
      port: containerPort
      scheme: 'HTTP'
    }
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
    successThreshold: 1
  }
] : []

resource containerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: name
  location: location
  tags: tags
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: external
        targetPort: containerPort
        transport: transport
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: registryConfig
      secrets: allSecrets
    }
    template: {
      containers: [
        {
          name: name
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: env
          probes: healthProbes
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: transport != 'tcp' ? [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ] : []
      }
    }
  }
}

output id string = containerApp.id
output name string = containerApp.name
output fqdn string = containerApp.properties.configuration.ingress.fqdn
output latestRevision string = containerApp.properties.latestRevisionName
