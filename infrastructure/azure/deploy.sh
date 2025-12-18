#!/bin/bash
# infrastructure/azure/deploy.sh
# Quick deployment script for BrandTruth AI to Azure
#
# Usage:
#   ./deploy.sh test    # Deploy to test environment
#   ./deploy.sh prod    # Deploy to production

set -e

ENVIRONMENT=${1:-test}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================"
echo "BrandTruth AI - Azure Deployment"
echo "Environment: $ENVIRONMENT"
echo "========================================"

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."

    if ! command -v az &> /dev/null; then
        echo "Error: Azure CLI not installed"
        echo "Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi

    if ! command -v terraform &> /dev/null; then
        echo "Error: Terraform not installed"
        echo "Install: brew install terraform"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo "Error: Docker not installed"
        exit 1
    fi

    # Check Azure login
    if ! az account show &> /dev/null; then
        echo "Not logged into Azure. Running az login..."
        az login
    fi

    echo "Prerequisites OK"
}

# Initialize Terraform
init_terraform() {
    echo ""
    echo "Initializing Terraform..."
    cd "$SCRIPT_DIR"
    terraform init -upgrade
}

# Plan deployment
plan_deployment() {
    echo ""
    echo "Planning deployment..."

    TFVARS_FILE="environments/${ENVIRONMENT}.tfvars"
    LOCAL_TFVARS="terraform.tfvars.local"

    if [ -f "$LOCAL_TFVARS" ]; then
        terraform plan -var-file="$TFVARS_FILE" -var-file="$LOCAL_TFVARS" -out=tfplan
    else
        terraform plan -var-file="$TFVARS_FILE" -out=tfplan
    fi
}

# Apply deployment
apply_deployment() {
    echo ""
    read -p "Apply this plan? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 0
    fi

    terraform apply tfplan
}

# Build and push Docker images
build_and_push_images() {
    echo ""
    echo "Building and pushing Docker images..."

    # Get ACR credentials
    ACR_NAME=$(terraform output -raw acr_login_server 2>/dev/null || echo "")

    if [ -z "$ACR_NAME" ]; then
        echo "Warning: ACR not found. Skipping image build."
        return
    fi

    ACR_USER=$(terraform output -raw acr_admin_username)
    ACR_PASS=$(terraform output -raw acr_admin_password)

    echo "Logging into ACR: $ACR_NAME"
    echo "$ACR_PASS" | docker login "$ACR_NAME" -u "$ACR_USER" --password-stdin

    cd "$ROOT_DIR"

    # Build API
    echo "Building API image..."
    docker build -t "$ACR_NAME/brandtruth-api:latest" -f Dockerfile .

    # Build Worker
    echo "Building Worker image..."
    docker build -t "$ACR_NAME/brandtruth-worker:latest" -f Dockerfile.worker .

    # Build Frontend
    echo "Building Frontend image..."
    API_URL=$(terraform -chdir="$SCRIPT_DIR" output -raw api_url 2>/dev/null || echo "http://localhost:8000")
    docker build \
        -t "$ACR_NAME/brandtruth-frontend:latest" \
        --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
        frontend/

    # Push images
    echo "Pushing images to ACR..."
    docker push "$ACR_NAME/brandtruth-api:latest"
    docker push "$ACR_NAME/brandtruth-worker:latest"
    docker push "$ACR_NAME/brandtruth-frontend:latest"

    echo "Images pushed successfully"
}

# Update Container Apps with new images
update_container_apps() {
    echo ""
    echo "Updating Container Apps..."

    RG_NAME="rg-brandtruth-${ENVIRONMENT}"
    ACR_NAME=$(terraform output -raw acr_login_server)

    # Update API
    echo "Updating API container app..."
    az containerapp update \
        --name "ca-api-brandtruth-${ENVIRONMENT}" \
        --resource-group "$RG_NAME" \
        --image "$ACR_NAME/brandtruth-api:latest" \
        --output none || echo "API update failed (may not exist yet)"

    # Update Worker
    echo "Updating Worker container app..."
    az containerapp update \
        --name "ca-worker-brandtruth-${ENVIRONMENT}" \
        --resource-group "$RG_NAME" \
        --image "$ACR_NAME/brandtruth-worker:latest" \
        --output none || echo "Worker update failed (may not exist yet)"

    # Update Frontend
    echo "Updating Frontend container app..."
    az containerapp update \
        --name "ca-frontend-brandtruth-${ENVIRONMENT}" \
        --resource-group "$RG_NAME" \
        --image "$ACR_NAME/brandtruth-frontend:latest" \
        --output none || echo "Frontend update failed (may not exist yet)"
}

# Print outputs
print_outputs() {
    echo ""
    echo "========================================"
    echo "Deployment Complete!"
    echo "========================================"
    echo ""
    echo "URLs:"
    terraform output urls
    echo ""
    echo "To view logs:"
    echo "  az containerapp logs show --name ca-api-brandtruth-${ENVIRONMENT} --resource-group rg-brandtruth-${ENVIRONMENT} --follow"
}

# Main
main() {
    check_prerequisites
    init_terraform
    plan_deployment
    apply_deployment

    read -p "Build and push Docker images? (yes/no): " build_images
    if [ "$build_images" == "yes" ]; then
        build_and_push_images
        update_container_apps
    fi

    print_outputs
}

main
