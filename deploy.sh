#!/bin/bash

# ================================================================
# ADK Self-Healing Agent - Complete Deployment Automation Script
# ================================================================
# 
# This script automates the complete deployment process:
# 1. GKE cluster creation
# 2. Docker image building and pushing
# 3. Bank of Anthos deployment
# 4. ADK agent deployment
# 5. Monitoring and validation
#
# Usage: ./deploy.sh [COMMAND] [OPTIONS]
# 
# Commands:
#   setup         - Initial setup and environment validation
#   cluster       - Create GKE cluster
#   bank-of-anthos - Deploy Bank of Anthos application
#   build         - Build and push Docker image
#   deploy        - Deploy ADK agent
#   cleanup       - Clean up resources
#   status        - Check deployment status
#
# Options:
#   --project-id    - GCP Project ID (required)
#   --cluster-name  - GKE cluster name (default: adk-cluster)
#   --region        - GCP region (default: us-central1)
#   --zone          - GCP zone (default: us-central1-a)
#   --image-tag     - Docker image tag (default: latest)
#   --dry-run       - Print commands without executing
#   --force         - Skip confirmations
#   --verbose       - Enable verbose logging
#
# Examples:
#   ./deploy.sh setup --project-id=my-project
#   ./deploy.sh cluster --project-id=my-project --cluster-name=my-cluster
#   ./deploy.sh build --image-tag=v1.0.0
#   ./deploy.sh cleanup --project-id=my-project --force
# ================================================================

set -e  # Exit on any error

# ----------------------------------------------------------------
# Configuration and Default Values
# ----------------------------------------------------------------

# Default configuration
DEFAULT_PROJECT_ID=""
DEFAULT_CLUSTER_NAME="adk-cluster"
DEFAULT_REGION="us-central1"
DEFAULT_ZONE="us-central1-a"
DEFAULT_IMAGE_TAG="latest"
DEFAULT_NAMESPACE="adk-agent"
DEFAULT_BANK_NAMESPACE="default"

# Slack integration defaults
DEFAULT_SLACK_WEBHOOK_URL=""
DEFAULT_SLACK_CHANNEL="#genral"
DEFAULT_SLACK_BOT_NAME="ADK Self-Healing Agent"

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/deployment.log"
DRY_RUN=false
FORCE=false
VERBOSE=false
FAST_MODE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ----------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "DEBUG") [[ $VERBOSE == true ]] && echo -e "${BLUE}[DEBUG]${NC} $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

run_command() {
    local cmd="$*"
    local timeout_seconds=300  # 5 minutes timeout
    log "DEBUG" "Executing: $cmd"
    
    if [[ $DRY_RUN == true ]]; then
        echo "[DRY-RUN] $cmd"
        return 0
    fi
    
    # Use timeout command to prevent hanging
    local full_cmd
    if [[ $VERBOSE == true ]]; then
        full_cmd="timeout $timeout_seconds bash -c '$cmd' 2>&1 | tee -a '$LOG_FILE'"
    else
        full_cmd="timeout $timeout_seconds bash -c '$cmd' >> '$LOG_FILE' 2>&1"
    fi
    
    if eval "$full_cmd"; then
        log "DEBUG" "Command completed successfully"
        return 0
    else
        local exit_code=$?
        if [[ $exit_code == 124 ]]; then
            log "ERROR" "Command timed out after $timeout_seconds seconds: $cmd"
        else
            log "ERROR" "Command failed with exit code $exit_code: $cmd"
        fi
        return $exit_code
    fi
}

confirm() {
    if [[ $FORCE == true ]]; then
        return 0
    fi
    
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "INFO" "Operation cancelled by user"
        exit 0
    fi
}

check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check required tools
    local tools=("gcloud" "kubectl" "docker")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log "ERROR" "$tool is not installed or not in PATH"
            exit 1
        fi
        log "DEBUG" "$tool found: $(command -v "$tool")"
    done
    
    # Check gcloud authentication
    log "DEBUG" "Checking gcloud authentication..."
    if ! timeout 30 gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        log "ERROR" "gcloud is not authenticated or authentication check timed out. Run 'gcloud auth login' first"
        exit 1
    fi
    
    # Validate project ID
    if [[ -z "$PROJECT_ID" ]]; then
        log "ERROR" "Project ID is required. Use --project-id=your-project-id"
        exit 1
    fi
    
    # Check if project exists and is accessible
    log "DEBUG" "Checking project accessibility..."
    if ! timeout 30 gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log "ERROR" "Project $PROJECT_ID not found or not accessible (or check timed out)"
        exit 1
    fi
    
    # Skip billing and quota checks that can be slow/problematic
    log "DEBUG" "Skipping billing and quota checks to prevent hanging..."
    log "WARN" "Note: Billing and quota checks skipped. Ensure your project has billing enabled and sufficient quotas."
    
    # Quick connectivity test
    log "DEBUG" "Testing basic connectivity to Google Cloud APIs..."
    if ! timeout 10 gcloud config list --format="value(core.project)" &> /dev/null; then
        log "WARN" "Basic gcloud connectivity test failed or timed out"
    fi
    
    log "INFO" "Prerequisites check passed"
}

enable_apis() {
    log "INFO" "Enabling required Google Cloud APIs..."
    
    local apis=(
        "container.googleapis.com"
        "cloudbuild.googleapis.com"
        "artifactregistry.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
        "aiplatform.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        log "DEBUG" "Enabling $api"
        local enable_cmd="gcloud services enable $api --project=$PROJECT_ID --quiet"
        if ! run_command "$enable_cmd"; then
            log "WARN" "Failed to enable $api, but continuing..."
        fi
    done
    
    # Wait a moment for APIs to be fully activated (reduced from 10 seconds)
    if [[ $FAST_MODE != true ]]; then
        log "INFO" "Waiting for APIs to be fully activated..."
        sleep 5
        
        # Quick verification of Artifact Registry API (with timeout)
        log "DEBUG" "Verifying Artifact Registry API access..."
        if ! timeout 15 gcloud artifacts repositories list --project="$PROJECT_ID" --location="$REGION" &> /dev/null; then
            log "WARN" "Artifact Registry API verification failed or timed out, but continuing..."
        else
            log "DEBUG" "Artifact Registry API is accessible"
        fi
    else
        log "INFO" "Fast mode: Skipping API activation wait"
    fi
    
    log "INFO" "APIs enabled successfully"
}

# ----------------------------------------------------------------
# Main Deployment Functions
# ----------------------------------------------------------------

setup_environment() {
    log "INFO" "Setting up deployment environment..."
    
    if [[ $FAST_MODE == true ]]; then
        log "INFO" "Fast mode enabled - skipping optional checks"
    fi
    
    check_prerequisites
    enable_apis
    
    # Set gcloud defaults
    run_command "gcloud config set project $PROJECT_ID"
    run_command "gcloud config set compute/region $REGION"
    run_command "gcloud config set compute/zone $ZONE"
    
    # Create Artifact Registry repository
    log "INFO" "Creating Artifact Registry repository..."
    log "DEBUG" "Checking if repository 'adk-agent' exists in region '$REGION'..."
    
    if ! timeout 30 gcloud artifacts repositories describe adk-agent --location="$REGION" --project="$PROJECT_ID" &> /dev/null; then
        log "INFO" "Repository does not exist, creating new repository..."
        local create_repo_cmd="gcloud artifacts repositories create adk-agent \
            --repository-format=docker \
            --location=$REGION \
            --project=$PROJECT_ID \
            --description='ADK Self-Healing Agent Docker images' \
            --quiet"
        
        log "DEBUG" "Running: $create_repo_cmd"
        run_command "$create_repo_cmd"
        
        # Verify creation
        if timeout 30 gcloud artifacts repositories describe adk-agent --location="$REGION" --project="$PROJECT_ID" &> /dev/null; then
            log "INFO" "Artifact Registry repository created successfully"
        else
            log "ERROR" "Failed to create Artifact Registry repository or verification timed out"
            exit 1
        fi
    else
        log "INFO" "Artifact Registry repository already exists"
    fi
    
    # Configure Docker authentication
    log "INFO" "Configuring Docker authentication for Artifact Registry..."
    local docker_auth_cmd="gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet"
    log "DEBUG" "Running: $docker_auth_cmd"
    
    if ! run_command "$docker_auth_cmd"; then
        log "WARN" "Docker authentication failed, but continuing. You may need to run this manually later:"
        log "WARN" "  gcloud auth configure-docker ${REGION}-docker.pkg.dev"
    else
        log "INFO" "Docker authentication configured successfully"
    fi
    
    log "INFO" "Environment setup completed"
}

create_cluster() {
    log "INFO" "Creating GKE cluster: $CLUSTER_NAME"
    
    # Check if cluster already exists
    if gcloud container clusters describe "$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
        log "WARN" "Cluster $CLUSTER_NAME already exists"
        confirm "Do you want to continue with existing cluster?"
    else
        # Create GKE cluster with ADK-optimized configuration
        local create_cmd="gcloud container clusters create-auto $CLUSTER_NAME \
            --project=$PROJECT_ID \
            --region=$REGION"
        
        log "INFO" "Creating cluster with configuration..."
        run_command "$create_cmd"
    fi
    
    # Get cluster credentials
    log "INFO" "Getting cluster credentials..."
    run_command "gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID"
    
    # Verify cluster connection
    run_command "kubectl cluster-info"
    
    log "INFO" "GKE cluster created and configured successfully"
}

deploy_bank_of_anthos() {
    log "INFO" "Deploying Bank of Anthos application..."
    
    # Create namespace
    run_command "kubectl create namespace $BANK_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
    
    # Clone Bank of Anthos if not exists
    if [[ ! -d "$SCRIPT_DIR/bank-of-anthos" ]]; then
        log "INFO" "Cloning Bank of Anthos repository..."
        run_command "git clone https://github.com/GoogleCloudPlatform/bank-of-anthos.git $SCRIPT_DIR/bank-of-anthos"
    fi
    
    # Deploy Bank of Anthos
    log "INFO" "Applying Bank of Anthos manifests..."
    run_command "kubectl apply -f $SCRIPT_DIR/bank-of-anthos/kubernetes-manifests -n $BANK_NAMESPACE"
    run_command "kubectl apply -f $SCRIPT_DIR/bank-of-anthos/extras/jwt/jwt-secret.yaml -n $BANK_NAMESPACE"
    
    # Wait for deployment to be ready
    log "INFO" "Waiting for Bank of Anthos services to be ready..."
    run_command "kubectl wait --for=condition=available --timeout=300s deployment --all -n $BANK_NAMESPACE"
    
    # Get frontend service IP
    log "INFO" "Getting Bank of Anthos frontend IP..."
    run_command "kubectl get services -n $BANK_NAMESPACE"
    
    log "INFO" "Bank of Anthos deployed successfully"
}

build_and_push_image() {
    log "INFO" "Building and pushing ADK agent Docker image..."
    
    local image_name="${REGION}-docker.pkg.dev/${PROJECT_ID}/adk-agent/self-healing-agent:${IMAGE_TAG}"
    
    # Check if docker buildx is available for multi-platform builds
    if docker buildx version &> /dev/null; then
        log "INFO" "Building Docker image with buildx for linux/amd64 platform: $image_name"
        run_command "docker buildx build --platform linux/amd64 -t $image_name -f $SCRIPT_DIR/Dockerfile $SCRIPT_DIR --load"
    else
        log "INFO" "Building Docker image with explicit platform for linux/amd64: $image_name"
        run_command "docker build --platform linux/amd64 -t $image_name -f $SCRIPT_DIR/Dockerfile $SCRIPT_DIR"
    fi
    
    # Push to Artifact Registry
    log "INFO" "Pushing image to Artifact Registry..."
    run_command "docker push $image_name"
    
    log "INFO" "Docker image built and pushed: $image_name"
    echo "IMAGE_NAME=$image_name" > "$SCRIPT_DIR/.env.deployment"
}

deploy_adk_agent() {
    log "INFO" "Deploying ADK Self-Healing Agent..."
    
    # Source image name from build step
    if [[ -f "$SCRIPT_DIR/.env.deployment" ]]; then
        source "$SCRIPT_DIR/.env.deployment"
    else
        IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/adk-agent/self-healing-agent:${IMAGE_TAG}"
    fi
    
    # Create namespace
    run_command "kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
    
    # Create service account with proper permissions
    create_service_account
    
    # Deploy using Helm if available, otherwise use kubectl
    if command -v helm &> /dev/null && [[ -d "$SCRIPT_DIR/helm" ]]; then
        deploy_with_helm
    else
        deploy_with_kubectl
    fi
    
    log "INFO" "ADK agent deployed successfully"
}

create_gcp_service_account() {
    log "INFO" "Creating GCP IAM service account and binding permissions..."
    
    local gcp_sa_name="adk-agent"
    local gcp_sa_email="${gcp_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
    
    # Create GCP service account if it doesn't exist
    if ! gcloud iam service-accounts describe "$gcp_sa_email" --project="$PROJECT_ID" &> /dev/null; then
        log "INFO" "Creating GCP service account: $gcp_sa_email"
        run_command "gcloud iam service-accounts create $gcp_sa_name \
            --display-name='ADK Self-Healing Agent' \
            --description='Service account for ADK agent to access GCP and GKE resources' \
            --project=$PROJECT_ID"
    else
        log "INFO" "GCP service account already exists: $gcp_sa_email"
    fi
    
    # Bind necessary IAM roles for GKE and monitoring
    local roles=(
        "roles/container.developer"
        "roles/monitoring.viewer"
        "roles/logging.viewer"
        "roles/compute.viewer"
        "roles/container.clusterViewer"
        "roles/aiplatform.user"
        "roles/ml.developer"
        "roles/vertexai.user"
    )
    
    for role in "${roles[@]}"; do
        log "DEBUG" "Binding role $role to $gcp_sa_email"
        run_command "gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member='serviceAccount:$gcp_sa_email' \
            --role='$role' \
            --quiet"
    done
    
    # Enable Workload Identity binding
    log "INFO" "Setting up Workload Identity binding..."
    run_command "gcloud iam service-accounts add-iam-policy-binding $gcp_sa_email \
        --role roles/iam.workloadIdentityUser \
        --member='serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/adk-agent]' \
        --project=$PROJECT_ID"
    
    log "INFO" "GCP service account setup completed"
}

create_service_account() {
    log "INFO" "Creating service account and RBAC..."
    
    # Create GCP IAM service account first
    create_gcp_service_account
    
    # Create Kubernetes service account with proper annotations
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: adk-agent
  namespace: $NAMESPACE
  annotations:
    iam.gke.io/gcp-service-account: adk-agent@${PROJECT_ID}.iam.gserviceaccount.com
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: adk-agent
rules:
# Core resources for service monitoring and management
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "namespaces"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# Pod logs access - CRITICAL for agent functionality
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get", "list"]
# Pod status and exec access for debugging
- apiGroups: [""]
  resources: ["pods/status", "pods/exec"]
  verbs: ["get", "create"]
# App deployments and replicasets
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
# Events for monitoring and alerting
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch", "create"]
# Metrics access
- apiGroups: ["metrics.k8s.io"]
  resources: ["pods", "nodes"]
  verbs: ["get", "list"]
# Nodes access for cluster-wide monitoring
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list", "watch"]
# Persistent volumes for storage monitoring
- apiGroups: [""]
  resources: ["persistentvolumes", "persistentvolumeclaims"]
  verbs: ["get", "list", "watch"]
# Ingress and network policies
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses", "networkpolicies"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
# Extensions and autoscaling
- apiGroups: ["extensions", "autoscaling"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
# Custom resources and CRDs (for service mesh, monitoring tools)
- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["get", "list", "watch"]
# RBAC permissions to manage other service accounts if needed
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: adk-agent
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: adk-agent
subjects:
- kind: ServiceAccount
  name: adk-agent
  namespace: $NAMESPACE
EOF
}

deploy_with_kubectl() {
    log "INFO" "Deploying with kubectl..."
    
    # Create deployment manifest
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adk-agent
  namespace: $NAMESPACE
  labels:
    app: adk-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: adk-agent
  template:
    metadata:
      labels:
        app: adk-agent
    spec:
      serviceAccountName: adk-agent
      containers:
      - name: adk-agent
        image: $IMAGE_NAME
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT
          value: "$PROJECT_ID"
        - name: ADK_K8S_NAMESPACE
          value: "$BANK_NAMESPACE"
        - name: ADK_CLUSTER_NAME
          value: "$CLUSTER_NAME"
        - name: ADK_REGION
          value: "$REGION"
        - name: ADK_AUTOPILOT_MODE
          value: "false"
        - name: PORT
          value: "8080"
        - name: HOST
          value: "0.0.0.0"
        # Kubernetes client configuration
        - name: KUBERNETES_SERVICE_HOST
          value: "kubernetes.default.svc"
        - name: KUBERNETES_SERVICE_PORT
          value: "443"
        # Enable in-cluster authentication
        - name: KUBERNETES_IN_CLUSTER
          value: "true"
        # Agent-specific configuration
        - name: ADK_MONITORING_ENABLED
          value: "true"
        - name: ADK_LOG_LEVEL
          value: "INFO"
        # Slack integration configuration
        - name: SLACK_WEBHOOK_URL
          value: "$SLACK_WEBHOOK_URL"
        - name: SLACK_CHANNEL
          value: "$SLACK_CHANNEL"
        - name: SLACK_BOT_NAME
          value: "$SLACK_BOT_NAME"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 900m
            memory: 2Gi
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: adk-agent
  namespace: $NAMESPACE
  labels:
    app: adk-agent
spec:
  selector:
    app: adk-agent
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  type: LoadBalancer
EOF
}

deploy_with_helm() {
    log "INFO" "Deploying with Helm..."
    
    run_command "helm upgrade --install adk-agent $SCRIPT_DIR/helm \
        --namespace $NAMESPACE \
        --create-namespace \
        --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/adk-agent/self-healing-agent \
        --set image.tag=$IMAGE_TAG \
        --set config.projectId=$PROJECT_ID \
        --set config.clusterName=$CLUSTER_NAME \
        --set config.region=$REGION \
        --set config.bankNamespace=$BANK_NAMESPACE"
}

check_deployment_status() {
    log "INFO" "Checking deployment status..."
    
    echo "================================"
    echo "GKE Cluster Status:"
    echo "================================"
    run_command "gcloud container clusters describe $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID --format='value(status)'"
    
    echo "================================"
    echo "Bank of Anthos Status:"
    echo "================================"
    run_command "kubectl get pods -n $BANK_NAMESPACE"
    
    echo "================================"
    echo "ADK Agent Status:"
    echo "================================"
    run_command "kubectl get pods -n $NAMESPACE"
    run_command "kubectl get services -n $NAMESPACE"
    
    # Get external IP
    local external_ip
    external_ip=$(kubectl get service adk-agent -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
    
    if [[ "$external_ip" != "Pending" && -n "$external_ip" ]]; then
        echo "================================"
        echo "🎉 Deployment Complete!"
        echo "================================"
        echo "ADK Agent URL: http://$external_ip"
        echo "API Documentation: http://$external_ip/docs"
        echo "Health Check: http://$external_ip/health"
        echo "Status API: http://$external_ip/status"
    else
        echo "================================"
        echo "⏳ Deployment in progress..."
        echo "================================"
        echo "External IP is still being assigned. Check status with:"
        echo "kubectl get services -n $NAMESPACE"
    fi
}

cleanup_resources() {
    log "INFO" "Cleaning up resources..."
    
    confirm "This will delete the entire GKE cluster and all resources. Are you sure?"
    
    # Delete ADK agent
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "INFO" "Deleting ADK agent..."
        run_command "kubectl delete namespace $NAMESPACE"
    fi
    
    # Delete Bank of Anthos
    if kubectl get namespace "$BANK_NAMESPACE" &> /dev/null; then
        log "INFO" "Deleting Bank of Anthos..."
        run_command "kubectl delete namespace $BANK_NAMESPACE"
    fi
    
    # Delete GKE cluster
    if gcloud container clusters describe "$CLUSTER_NAME" --region="$REGION" --project="$PROJECT_ID" &> /dev/null; then
        log "INFO" "Deleting GKE cluster..."
        run_command "gcloud container clusters delete $CLUSTER_NAME --region=$REGION --project=$PROJECT_ID --quiet"
    fi
    
    # Clean up local files
    rm -f "$SCRIPT_DIR/.env.deployment"
    
    log "INFO" "Cleanup completed"
}

debug_environment() {
    log "INFO" "Running environment diagnostics..."
    
    echo "================================"
    echo "Environment Debug Information"
    echo "================================"
    
    echo "Current user: $(whoami)"
    echo "Current directory: $(pwd)"
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "gcloud version: $(gcloud version --format='value(Google Cloud SDK)')"
    
    echo "================================"
    echo "Authentication Status"
    echo "================================"
    gcloud auth list
    
    echo "================================"
    echo "Current Project Configuration"
    echo "================================"
    gcloud config list
    
    echo "================================"
    echo "Project Information"
    echo "================================"
    gcloud projects describe "$PROJECT_ID" 2>/dev/null || echo "Failed to describe project"
    
    echo "================================"
    echo "Enabled APIs"
    echo "================================"
    gcloud services list --enabled --project="$PROJECT_ID" --filter="name:(artifactregistry OR container)" --format="table(name,title)"
    
    echo "================================"
    echo "Artifact Registry Repositories"
    echo "================================"
    gcloud artifacts repositories list --project="$PROJECT_ID" --location="$REGION" 2>/dev/null || echo "Failed to list repositories"
    
    echo "================================"
    echo "Network Connectivity Test"
    echo "================================"
    if command -v curl &> /dev/null; then
        echo "Testing connectivity to Google APIs..."
        curl -s -o /dev/null -w "artifactregistry.googleapis.com: %{http_code}\n" "https://artifactregistry.googleapis.com/" || echo "Network test failed"
    fi
    
    log "INFO" "Debug information collected"
}

# ----------------------------------------------------------------
# Command Line Parsing
# ----------------------------------------------------------------

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project-id=*)
                PROJECT_ID="${1#*=}"
                shift
                ;;
            --cluster-name=*)
                CLUSTER_NAME="${1#*=}"
                shift
                ;;
            --region=*)
                REGION="${1#*=}"
                shift
                ;;
            --zone=*)
                ZONE="${1#*=}"
                shift
                ;;
            --image-tag=*)
                IMAGE_TAG="${1#*=}"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --fast)
                FAST_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                if [[ -z "$COMMAND" ]]; then
                    COMMAND="$1"
                else
                    log "ERROR" "Unknown argument: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Set defaults
    PROJECT_ID="${PROJECT_ID:-$DEFAULT_PROJECT_ID}"
    CLUSTER_NAME="${CLUSTER_NAME:-$DEFAULT_CLUSTER_NAME}"
    REGION="${REGION:-$DEFAULT_REGION}"
    ZONE="${ZONE:-$DEFAULT_ZONE}"
    IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"
    NAMESPACE="${NAMESPACE:-$DEFAULT_NAMESPACE}"
    BANK_NAMESPACE="${BANK_NAMESPACE:-$DEFAULT_BANK_NAMESPACE}"
    
    # Slack integration defaults
    SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-$DEFAULT_SLACK_WEBHOOK_URL}"
    SLACK_CHANNEL="${SLACK_CHANNEL:-$DEFAULT_SLACK_CHANNEL}"
    SLACK_BOT_NAME="${SLACK_BOT_NAME:-$DEFAULT_SLACK_BOT_NAME}"
}

show_help() {
    cat <<EOF
ADK Self-Healing Agent Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  setup         - Initial setup and environment validation
  cluster       - Create GKE cluster
  bank-of-anthos - Deploy Bank of Anthos application
  build         - Build and push Docker image
  deploy        - Deploy ADK agent
  cleanup       - Clean up all resources
  status        - Check deployment status
  debug         - Run environment diagnostics

Options:
  --project-id=ID     - GCP Project ID (required)
  --cluster-name=NAME - GKE cluster name (default: adk-cluster)
  --region=REGION     - GCP region (default: us-central1)
  --zone=ZONE         - GCP zone (default: us-central1-a)
  --image-tag=TAG     - Docker image tag (default: latest)
  --dry-run           - Print commands without executing
  --force             - Skip confirmations
  --verbose           - Enable verbose logging
  --fast              - Skip optional checks that may hang
  --help              - Show this help

Examples:
  $0 setup --project-id=my-project
  $0 cluster --project-id=my-project --cluster-name=my-cluster
  $0 build --image-tag=v1.0.0
  $0 cleanup --project-id=my-project --force

Recommended workflow:
  1. $0 setup --project-id=my-project
  2. $0 cluster --project-id=my-project (wait for completion ~10-20min)
  3. $0 bank-of-anthos --project-id=my-project
  4. $0 build --project-id=my-project
  5. $0 deploy --project-id=my-project
EOF
}

# ----------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------

main() {
    # Initialize log file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deployment script started" > "$LOG_FILE"
    
    parse_arguments "$@"
    
    if [[ -z "$COMMAND" ]]; then
        log "ERROR" "No command specified. Use --help for usage information."
        exit 1
    fi
    
    log "INFO" "Starting ADK Self-Healing Agent deployment..."
    log "INFO" "Command: $COMMAND"
    log "INFO" "Project ID: $PROJECT_ID"
    log "INFO" "Cluster Name: $CLUSTER_NAME"
    log "INFO" "Region: $REGION"
    log "INFO" "Image Tag: $IMAGE_TAG"
    
    case $COMMAND in
        "setup")
            setup_environment
            ;;
        "cluster")
            setup_environment
            create_cluster
            ;;
        "bank-of-anthos")
            deploy_bank_of_anthos
            ;;
        "build")
            build_and_push_image
            ;;
        "deploy")
            deploy_adk_agent
            ;;
        "cleanup")
            cleanup_resources
            ;;
        "status")
            check_deployment_status
            ;;
        "debug")
            debug_environment
            ;;
        *)
            log "ERROR" "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
    
    log "INFO" "Command '$COMMAND' completed successfully!"
}

# Run main function with all arguments
main "$@"
