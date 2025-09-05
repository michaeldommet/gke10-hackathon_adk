# ADK Self-Healing Agent

An AI-powered autonomous operations agent built with Google's Agent Development Kit (ADK) that enhances Bank of Anthos deployments on GKE with intelligent monitoring, analysis, and self-healing capabilities. Features **AlertManager webhook integration** for real-time alert processing and automated incident response.

## Overview

The ADK Self-Healing Agent automatically monitors, detects, and remediates operational failures in microservices using Google AI (Gemini) for intelligent anomaly detection and decision-making. Built on Google's Agent Development Kit (ADK), it provides enterprise-grade autonomous operations with **AlertManager integration** for immediate response to Prometheus alerts.

## 🎯 Two Ways to Interact with the AI Agent

### 1. **Interactive Web UI** 🌐
**For Human Users**: Direct conversation with the AI agent through a web interface
- **Use Case**: Manual troubleshooting, asking questions, exploring insights
- **Features**: Full conversational AI, data exploration, manual analysis
- **Example**: "What's the current status of the frontend service?" or "Analyze recent errors in Bank of Anthos"

### 2. **AlertManager Webhook Integration** 🚨
**For Automated Systems**: Prometheus AlertManager sends alerts directly to the agent
- **Use Case**: Automated incident response, real-time alert processing
- **Features**: Background processing, persistent sessions, automatic workflows
- **Example**: AlertManager detects high CPU → Agent analyzes → Creates Jira ticket → Provides recommendations

```
┌─────────────────┐         ┌───────────────────┐         ┌─────────────────┐
│   Human User    │────────▶│   ADK AI Agent    │◀────────│  AlertManager   │
│                 │ Web UI  │                   │ Webhook │   (Prometheus)  │
│ Manual queries  │         │  Same AI Brain    │         │ Automated alerts│
│ Exploration     │         │  Same responses   │         │ Real-time ops   │
└─────────────────┘         └───────────────────┘         └─────────────────┘
```

**Both methods use the same AI agent and provide the same intelligent analysis** - the only difference is the interaction method!


### Supported Bank of Anthos Services

The agent automatically processes alerts for these services:
- `frontend`, `userservice`, `contacts`
- `balancereader`, `balance-reader`
- `ledgerwriter`, `ledger-writer` 
- `transactionhistory`, `transaction-history`
- `loadgenerator`, `load-generator`
- `accounts-db`, `ledger-db` (StatefulSets)

## Features

- 🤖 **ADK-Powered AI Agents**: Multi-agent architecture using Google's Agent Development Kit
- 🚨 **AlertManager Integration**: Real-time webhook processing for Prometheus alerts with automatic workflows
- 🔍 **Intelligent Monitoring**: Collects metrics, logs, and Kubernetes events with smart analysis
- 🧠 **Gemini Integration**: Uses Google Gemini via **Vertex AI** for advanced anomaly detection
- 🔧 **Automated Remediation**: Executes corrective actions (pod restarts, scaling, notifications)
- 🎯 **Optimized Jira Integration**: Fast incident management via Jira MCP server with performance optimizations
- 💬 **Rich Slack Notifications**: Real-time alerts with severity-based formatting and customizable channels
- 🛡️ **Autopilot Mode**: Simple on/off automation control (safe mode vs full automation)
- 🌐 **ADK Web Interface**: Built-in web interface for monitoring and control



## Architecture

![ADK Self-Healing Agent Architecture](architecture_diagram%20.png)

```
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ User Interaction  │    │ Monitoring Agent │    │ Analysis Agent   │    │ Decision Agent   │
│ (Web UI)          │───▶│ (Collects Data)  │───▶│ (AI Analysis)    │───▶│ (Takes Action)   │
│ Alertmanager      │    │ + Metrics/Logs   │    │                  │    │                  │
│ (Prometheus)      │    │ + Pod Status     │    │                  │    │                  │
└───────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
        │                          │                          │                   │
        ▼                          ▼                          ▼                   ▼
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Alert Input       │    │ get_service_...  │    │ get_service_...  │    │ scale_deployment │
│ (Events/Alerts)   │    │ get_pod_status   │    │ Insights Passed  │    │ send_alert       │
│                   │    │ get_service_logs │    │ to Decision      │    │ Jira MCP Server  │
└───────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
                                                                                  │
                                                                                  ▼
                                                                        ┌──────────────────┐
                                                                        │ Jira MCP Server  │
                                                                        │ + Incident Mgmt  │
                                                                        │ + Slack Webhooks │
                                                                        │ (create/update)  │
                                                                        └──────────────────┘

```

### Real-World Workflow Implementation

**Step 1: Alert Trigger**
- Prometheus monitors Bank of Anthos services
- AlertManager detects issues and sends webhooks
- FastAPI endpoint `/alertmanager` receives real-time alerts

**Step 2: Session Management**
- Agent creates/reuses persistent AlertManager session
- Maintains context across multiple related alerts
- Filters for Bank of Anthos services only

**Step 3: AI Analysis**
- Analysis agent processes alert data using Gemini AI
- Determines severity, impact, and root cause analysis


**Step 4: Automated Decision**
- Decision agent evaluates autopilot mode settings
- **Safe Mode**: Creates JIRA incidents for human review
- **Full Mode**: Executes remediation + creates JIRA tickets

**Step 5: Action Execution**
- Kubernetes API calls for pod restarts, scaling
- JIRA ticket creation with detailed incident information
- Real-time monitoring of remediation progress

**Step 6: Verification & Closure**
- Termination agent verifies issue resolution
- Updates JIRA tickets with resolution status


## AlertManager Integration

The agent includes a **FastAPI webhook receiver** that processes AlertManager notifications in real-time:

### Alert Processing Flow
1. **Prometheus** detects issues in Bank of Anthos services
2. **AlertManager** sends webhook to ADK agent (`/alertmanager` endpoint)
3. **Agent filters** alerts for Bank of Anthos services only
4. **Automatic workflow** triggers based on alert severity:
   - **Critical/High**: Immediate remediation + Jira incidents
   - **Medium**: Jira ticket creation + monitoring
   - **Low**: Logging and trend analysis
5. **Session management** maintains context across alert processing

### Webhook Configuration
```yaml
# AlertManager webhook configuration
receivers:
- name: 'bank-of-anthos-webhook'
  webhook_configs:
  - url: 'http://adk-agent.adk-agent.svc.cluster.local/alertmanager'
    http_config:
      timeout: 10s
```

## Quick Start - Step-by-Step Deployment

### Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- `kubectl` installed
- `docker` installed
- Sufficient GCP quotas for GKE cluster

### Recommended Deployment Workflow


```bash
# Clone the repository
git clone <repository-url>
cd gke10-hackathon_adk

# Step 1: Setup environment and enable APIs
./deploy.sh setup --project-id=your-project-id

# Step 2: Create GKE cluster (10-20 minutes)
./deploy.sh cluster --project-id=your-project-id --cluster-name=my-cluster

```

⚠️ **Note:** If cluster creation times out with `[ERROR] Command timed out after 300 seconds: gcloud container clusters create-auto adk-cluster`, check if the cluster was actually created:

```bash
# Check if cluster exists
gcloud container clusters list --project=your-project-id

# If cluster exists, get credentials manually
gcloud container clusters get-credentials adk-cluster --region=us-central1 --project=your-project-id
```

Sometimes cluster creation takes longer than the timeout but still succeeds. Always verify the cluster status before retrying.

```bash
# Step 3: Deploy Bank of Anthos
./deploy.sh bank-of-anthos

# Step 4: Build and push ADK agent image
./deploy.sh build --project-id=your-project-id

# Step 5: Deploy ADK agent
./deploy.sh deploy

# Step 6: Check deployment status
./deploy.sh status
```

### Testing AlertManager Integration

Test the AlertManager webhook integration with this curl command:

```bash
curl -X POST "http://127.0.0.1:8080/alertmanager" \
  -H "Content-Type: application/json" \
  -H "User-Agent: Alertmanager/0.25.0" \
  -d '{
    "receiver": "bank-of-anthos-webhook",
    "status": "firing", 
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighCPUUsage",
          "service": "frontend",
          "namespace": "bank-of-anthos",
          "severity": "high",
          "instance": "frontend-7f585f45df-5xsx5:8080",
          "job": "frontend"
        },
        "annotations": {
          "summary": "High CPU usage detected on frontend service",
          "description": "Frontend service CPU usage is 92% for the last 5 minutes. This may impact user experience and response times."
        },
        "startsAt": "2025-09-01T10:30:00.000Z",
        "generatorURL": "http://prometheus:9090/graph?g0.expr=cpu_usage%7Bservice%3D%22frontend%22%7D",
        "fingerprint": "frontend-high-cpu-001"
      }
    ],
    "groupLabels": {
      "alertname": "HighCPUUsage"
    },
    "commonLabels": {
      "service": "frontend",
      "severity": "high"
    },
    "commonAnnotations": {
      "summary": "High CPU usage detected on frontend service"
    },
    "externalURL": "http://alertmanager:9093",
    "version": "4",
    "groupKey": "{}:{alertname=\"HighCPUUsage\"}",
    "truncatedAlerts": 0
  }'
```

**Expected Response:** `{"status":"success","message":"Processed 1 alerts"}`

### Important Notes

⚠️ **Instance Names**: Make sure the `instance` field in your alerts contains actual pod names or IP addresses from your GKE cluster. The agent validates these against real Kubernetes resources.

```bash
# Monitor agent logs for alert processing
kubectl logs -f deployment/adk-agent -n adk-agent

# Check agent health and status
curl http://<agent-ip>/health
```

🔍 **Monitoring Results**: After sending an alert, check the console output for:
```
✅ Agent processed alert: HighCPUUsage
🌐 Full response available at: http://localhost:8080/apps/adk_self_healing_agent/users/alertmanager-system/sessions/alertmanager-persistent-session
```

### Deployment Options

```bash
# Custom configuration
./deploy.sh cluster \
  --project-id=my-project \
  --cluster-name=my-cluster \
  --region=us-central1 \
  --verbose

# Build with specific tag
./deploy.sh build --project-id=my-project --image-tag=v1.0.0

# Dry run (see what would be executed)
./deploy.sh setup --project-id=my-project --dry-run

# Force mode (skip confirmations)
./deploy.sh cleanup --project-id=my-project --force

# Fast mode (skip optional checks)
./deploy.sh setup --project-id=my-project --fast
```

## AI Provider Setup

The ADK Self-Healing Agent uses **Vertex AI** by default for production deployments for better performance:

### Alternative: Google AI Studio (Development Only)
For local development, you can use Google AI Studio:
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set in your `.env`:
   ```bash
   USE_GOOGLE_AI_STUDIO=true
   GOOGLE_AI_API_KEY=your-api-key-here
   ```

## Manual Local Development

If you prefer manual setup over automated deployment:

## Manual Local Development

If you prefer manual setup over automated deployment:

### Prerequisites
- Python 3.11+
- Google Cloud Project
- `gcloud` CLI authenticated

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd gke10-hackathon_adk
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run with ADK**:
   ```bash
   adk web
   or 
   python main.py
   ```

4. **Access the agent**:
   - ADK Web Interface: http://localhost:8000 (via `adk web`)
   - Configuration Test: `python test_adk_agent.py`

## Using the ADK Agent

### ADK Web Interface
Access the standard ADK web interface at `http://localhost:8000` when running locally with `adk web`.

### Key Features
- **Multi-Agent Workflow**: Complete monitoring → analysis → decision → termination workflow implementation
- **Incident Management**: Automatic Jira ticket creation with intelligent severity classification  
- **Autopilot Control**: Simple toggle between safe mode (alerts only) and full automation (including remediation actions)
- **AI-Powered Analysis**: Gemini-driven anomaly detection and remediation recommendations
- **ADK Integration**: Leverages Google's Agent Development Kit for agent orchestration

### Configuration Options

#### Autopilot Control
```bash
# Safe mode (alerts + Jira incidents only - no pod restarts/scaling)
ADK_AUTOPILOT_MODE=false

# Full automation (enables pod restarts, scaling, and all remediation actions)
ADK_AUTOPILOT_MODE=true
```

#### Optimized Jira Integration
```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_TOKEN=your-api-token
ATLASSIAN_OAUTH_CLOUD_ID=your-cloud-id
```

**Performance Optimization**: The agent now uses standard issue types ("Task", "Story", "Bug") by default to avoid slow API metadata calls. The `getJiraProjectIssueTypesMetadata` tool is only used as fallback when needed.
some times the Atlassian MCP is timing out.

#### Slack Integration
```bash
# Real-time notifications to Slack channels
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts
SLACK_BOT_NAME=ADK Self-Healing Agent
```

**Rich Notifications**: The agent sends beautifully formatted messages with:
- 🚨 **Severity-based colors and emojis** (Critical: red 🚨, High: orange ⚠️, Medium: gold ⚡, Low: green ℹ️)
- 📋 **Structured alert details** with service, cluster, and error information
- ⏰ **Timestamps and resolution status** updates
- 🤖 **Consistent branding** with customizable bot name and channel routing

#### AlertManager Webhook Configuration
```bash
# Agent listens on these endpoints:
# - /alertmanager         - AlertManager webhook receiver
# - /health              - Health check for Kubernetes probes  
# - /                    - Root status endpoint

# AlertManager webhook URL (adjust for your deployment):
http://adk-agent.adk-agent.svc.cluster.local/alertmanager
```

## Agent Interaction

The ADK agent provides multiple interaction methods:

### AlertManager Integration (Production)
**Primary use case**: Real-time alert processing from Prometheus/AlertManager
```bash
# AlertManager sends webhooks to:
POST http://adk-agent-service/alertmanager

# Example alert processing flow:
# 1. Prometheus detects high CPU in frontend service
# 2. AlertManager sends webhook to ADK agent
# 3. Agent creates persistent session and processes alert
# 4. AI analysis determines remediation strategy
# 5. Automatic actions taken based on severity and autopilot mode
```

### ADK Web Interface (Development/Testing)
```bash
# Access the standard ADK web interface
kubectl port-forward -n adk-agent service/adk-agent 8080:80
# Then visit: http://localhost:8080
```

### Direct API Access
```bash
# Health check
curl http://adk-agent-service/health

# Root status
curl http://adk-agent-service/

# Test webhook (use test-alertmanager-webhooks.sh)
./test-alertmanager-webhooks.sh
```

## Demo Scenarios

### Scenario 1: AlertManager Webhook Processing (Primary Use Case)
1. **Alert Generation**: Prometheus detects CPU > 80% in Bank of Anthos frontend service
2. **AlertManager Webhook**: Sends webhook to ADK agent `/alertmanager` endpoint
3. **Session Management**: Agent creates or reuses persistent session for AlertManager
4. **Service Filtering**: Agent processes only Bank of Anthos service alerts
5. **AI Analysis**: Gemini AI analyzes alert context, severity, and impact
6. **Automated Response**:
   - **Safe Mode (OFF)**: Creates optimized Jira incident for human review
   - **Full Mode (ON)**: Executes remediation (pod restart, scaling) + creates Jira ticket
7. **Resolution Tracking**: Agent verifies resolution and updates incidents

### Scenario 2: Local Development and Testing
```bash
# Test AlertManager webhook integration
./test-alertmanager-webhooks.sh

# Monitor agent processing in real-time
kubectl logs -f deployment/adk-agent -n adk-agent

# Check agent health and endpoints
curl http://localhost:8080/health
curl http://localhost:8080/
```

### Scenario 3: Manual Agent Testing via ADK Interface
```bash
# Local development with ADK web interface
python main.py
# Visit: http://localhost:8080

# Test agent configuration
python test_vertex_ai.py
```

## Troubleshooting

### Common Issues

1. **Deployment fails**: Check GCP quotas and permissions
2. **Agent not starting**: Verify Vertex AI API is enabled and IAM permissions
3. **AlertManager webhooks not working**: Check network connectivity and endpoint URLs
4. **JIRA integration slow**: Agent now uses optimized issue type selection for faster processing
5. **Health checks failing**: Ensure `/health` endpoint is accessible (added in recent updates)

### Debug Commands
```bash
# Check cluster and agent status
kubectl get pods -n adk-agent
kubectl get pods -n bank-of-anthos
kubectl get services -n adk-agent

# View agent logs (especially for webhook processing)
kubectl logs deployment/adk-agent -n adk-agent -f

# Test AlertManager webhook locally
./test-alertmanager-webhooks.sh

# Check agent endpoints
kubectl port-forward -n adk-agent service/adk-agent 8080:80
curl http://localhost:8080/health
curl http://localhost:8080/

# Verify Vertex AI permissions
kubectl exec -it deployment/adk-agent -n adk-agent -- python test_vertex_ai.py
```

## Development Status

- ✅ **AlertManager Integration**: FastAPI webhook receiver with real-time alert processing
- ✅ **Session Management**: Persistent AlertManager sessions for context continuity
- ✅ **ADK Integration**: Complete agent framework implementation with web interface
- ✅ **Multi-Agent Architecture**: Monitoring → Analysis → Decision → Termination workflow
- ✅ **Gemini AI Integration**: Vertex AI with intelligent analysis and centralized configuration
- ✅ **Optimized Jira Integration**: Fast incident management with performance optimizations
- ✅ **Health Endpoints**: Kubernetes-ready health checks and status endpoints
- ✅ **Simple Autopilot Mode**: On/off toggle for safe vs full automation
- ✅ **Step-by-Step Deployment**: Reliable deployment process (removed problematic `all` command)
- ✅ **Production Ready**: GKE deployment with proper RBAC, IAM, and Workload Identity
- ✅ **Comprehensive Testing**: AlertManager webhook test suite and validation scripts

## Technology Stack

- **AI Framework**: Google Agent Development Kit (ADK)
- **AI Models**: Google Gemini via Vertex AI
- **Webhook Processing**: FastAPI with async alert handling
- **Backend**: Python 3.11, Pydantic, httpx for internal API calls
- **Integration**: Jira MCP Server (optimized), Kubernetes API
- **Deployment**: Docker, GKE Autopilot, Helm
- **Monitoring**: Google Cloud Operations, Prometheus/AlertManager integration
- **Testing**: pytest, pytest-asyncio, webhook test suite

## Next Steps

1. ✅ **AlertManager Integration**: Complete real-time webhook processing
2. ✅ **Production Deployment**: Reliable step-by-step deployment pipeline  
3. ✅ **Performance Optimization**: Fast JIRA integration with reduced API calls
4. 🔄 **Enhanced Monitoring Dashboard**: Extend ADK web interface with AlertManager metrics
5. 🔄 **Multi-Cluster Support**: Extend AlertManager integration to multiple GKE clusters
6. 🔄 **Advanced Alert Routing**: Implement complex alert filtering and routing rules
7. 🔄 **Predictive Alerting**: Add machine learning for predictive failure detection

## Files Structure

```
├── deploy.sh                      # Main deployment automation script (step-by-step)
├── main.py                        # FastAPI app with AlertManager webhook integration
├── requirements.txt               # Python dependencies
├── env.example                    # Complete environment configuration template
├── .gitignore                     # Comprehensive gitignore for security
├── Dockerfile                     # Container image definition with health endpoints
├── alertmanager-config.yaml       # AlertManager configuration example
├── bank-of-anthos/                # Bank of Anthos application (git submodule)
├── adk_self_healing_agent/        # ADK agent source code
│   ├── __main__.py                # Agent entry point
│   ├── agent.py                   # Main agent definition
│   ├── config.py                  # Configuration management
│   ├── prompt.py                  # Agent prompts and instructions
│   ├── .env                       # Agent-specific environment variables
│   ├── sub_agents/                # Specialized sub-agents
│   │   ├── analysis/              # AI analysis agent
│   │   ├── decision/              # Optimized decision agent with fast JIRA
│   │   ├── monitoring/            # Monitoring and data collection agent
│   │   └── termination/           # Resolution verification agent
│   └── tools/                     # ADK tools and integrations
└── venv/                          # Python virtual environment (if using local dev)
```

## 🔧 Troubleshooting AlertManager Integration

### Common Issues

#### 1. **Webhook Timeout Errors**
```
⏰ Timeout processing alert: HighCPUUsage
```
**Solution**: This is normal! The agent needs time (up to 2 minutes) to collect real metrics and logs from Kubernetes and Google Cloud. The alert is still being processed in the background.

**Verification**: Check the console for:
```
✅ Background alert processing completed
🌐 Full response available at: http://localhost:8080/apps/...
```

#### 2. **Instance Name Validation Failures**
```
⏭️ Skipping non-Bank of Anthos service. Labels: {'instance': 'invalid-pod-name'}
```
**Solution**: Ensure your alert `instance` field contains actual pod names from your GKE cluster:
- ✅ Good: `frontend-7f585f45df-5xsx5:8080`
- ✅ Good: `accounts-db-0`
- ❌ Bad: `fake-pod-name` or generic hostnames

**Check your pods**: `kubectl get pods -n bank-of-anthos`

#### 3. **Session Not Found in Web UI**
**Solution**: The session is created automatically. If you don't see results in the web UI:

1. **Check session creation**:
```bash
python test-web-ui.py
```

2. **Verify the direct session URL**:
```
http://localhost:8080/apps/adk_self_healing_agent/users/alertmanager-system/sessions/alertmanager-persistent-session
```

3. **Restart the server** if sessions aren't persisting:
```bash
python main.py
```

#### 4. **Authentication Errors (Google Cloud)**
```
❌ Failed to create AlertManager session: google.auth.exceptions.TransportError
```
**Solution**: The agent gracefully falls back to Kubernetes-only mode. Ensure your GKE cluster authentication is working:
```bash
gcloud container clusters get-credentials CLUSTER_NAME --zone=ZONE --project=PROJECT_ID
kubectl get pods  # Should work without errors
```

#### 5. **No Alerts Being Processed**
**Verification Steps**:

1. **Test webhook endpoint**:
```bash
curl -s http://localhost:8080/health | jq
```

2. **Check service filtering**:
The agent only processes these Bank of Anthos services:
- `frontend`, `userservice`, `contacts`
- `balancereader`, `ledgerwriter`, `transactionhistory`
- `loadgenerator`, `accounts-db`, `ledger-db`

3. **Verify alert format** matches the example curl command above

### Debug Mode

Enable verbose logging by checking the console output:
```
🚨 Received 1 alerts from AlertManager
📋 Processing alert: {'alertname': 'HighCPUUsage', 'service': 'frontend', ...}
🎯 Bank of Anthos alert detected for: frontend
🔄 Created async task for alert processing - processing in background
📤 Sending to ADK endpoint with session: alertmanager-persistent-session
✅ Agent processed alert: HighCPUUsage
🌐 Full response available at: http://localhost:8080/apps/...
✅ Background alert processing completed
```

### Quick Health Check

```bash
# Test all endpoints
curl -s http://localhost:8080/health | jq
curl -s http://localhost:8080/status | jq
curl -s http://localhost:8080/ | jq

# Test session creation
python test-web-ui.py

# Test alert processing
python test-alertmanager.py
```

## Contributing

This is a hackathon project. See `tasks.md` for implementation progress and `design.md` for detailed architecture.

## License

MIT License - Hackathon Project
