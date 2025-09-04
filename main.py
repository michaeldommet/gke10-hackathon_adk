import os
import uvicorn
import httpx
import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import List, Dict

# Import the ADK function to create the FastAPI app
from google.adk.cli.fast_api import get_fast_api_app

# --- Configuration ---
# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# IMPORTANT: Set this to the name of your agent's directory.
# For example, if your agent is in a folder named 'alert_agent',
# set this value to "alert_agent".
AGENT_NAME = "adk_self_healing_agent"

# Example session service URI (e.g., "sqlite:///sessions.db" for persistence)
SESSION_SERVICE_URI = ""

# Allowed origins for CORS. Using ["*"] is permissive for development.
ALLOWED_ORIGINS = ["*"]

# Set to True to serve the ADK web interface, False otherwise
SERVE_WEB_INTERFACE = True

# --- AlertManager Session Configuration ---
# These will be initialized once at startup and reused for all alerts
ALERTMANAGER_APP_NAME = AGENT_NAME
ALERTMANAGER_USER_ID = "alertmanager-system"
ALERTMANAGER_SESSION_ID = "alertmanager-persistent-session"

# Track session creation status
session_created = False


# --- Pydantic Models for Alertmanager Webhook ---
# These models define and validate the structure of the incoming JSON
# payload from Alertmanager, making the code safer and easier to work with.

class Alert(BaseModel):
    """Represents a single alert from Prometheus."""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str = ""
    endsAt: str = ""
    generatorURL: str = ""
    fingerprint: str = ""

class AlertmanagerWebhookPayload(BaseModel):
    """Represents the full payload sent by Alertmanager to the webhook."""
    version: str = "4"
    groupKey: str = "default"
    truncatedAlerts: int = Field(0, alias="truncatedAlerts")
    status: str = "firing"
    receiver: str = "webhook"
    groupLabels: Dict[str, str] = {}
    commonLabels: Dict[str, str] = {}
    commonAnnotations: Dict[str, str] = {}
    externalURL: str = ""
    alerts: List[Alert]


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up - AlertManager session will be created on first alert...")
    yield
    # Shutdown
    print("🛑 Shutting down...")

async def ensure_session_exists():
    """Ensure the AlertManager session exists, create it if needed."""
    global session_created
    
    if session_created:
        return True
        
    try:
        session_url = f"http://localhost:8080/apps/{ALERTMANAGER_APP_NAME}/users/{ALERTMANAGER_USER_ID}/sessions/{ALERTMANAGER_SESSION_ID}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(session_url)
            if response.status_code == 200:
                print(f"✅ AlertManager session created: {ALERTMANAGER_SESSION_ID}")
                session_created = True
                return True
            elif response.status_code == 409:
                print(f"✅ AlertManager session already exists: {ALERTMANAGER_SESSION_ID}")
                session_created = True
                return True
            else:
                print(f"⚠️  Session creation response: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"❌ Failed to create AlertManager session: {e}")
        return False


# --- ADK FastAPI App Initialization ---
# This function from the ADK library builds the FastAPI application and
# sets up all the necessary API endpoints for your agent(s).
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
    lifespan=lifespan,
)

# --- Simplified Agent Interaction ---
async def send_alert_to_agent(alert: Alert):
    """Send alert to agent using the persistent session."""
    try:
        print(f"🔄 Starting alert processing for: {alert.labels.get('alertname', 'Unknown')}")
        
        # Ensure session exists before sending alert
        if not await ensure_session_exists():
            print("❌ Cannot send alert - session creation failed")
            return
            
        # Create a comprehensive prompt from the alert
        alert_name = alert.labels.get('alertname', 'Unknown Alert')
        service = alert.labels.get('service', alert.labels.get('deployment', alert.labels.get('pod', 'unknown')))
        severity = alert.labels.get('severity', 'warning')
        summary = alert.annotations.get('summary', 'No summary')
        description = alert.annotations.get('description', 'No description')
        
        # Include more context for Bank of Anthos services
        deployment = alert.labels.get('deployment', 'unknown')
        pod = alert.labels.get('pod', 'unknown')
        namespace = alert.labels.get('namespace', 'unknown')
        
        prompt = f"""🚨 PROMETHEUS ALERT RECEIVED

Alert: {alert_name}
Service: {service}
Deployment: {deployment}
Pod: {pod}
Namespace: {namespace}
Severity: {severity}
Status: {alert.status}
Summary: {summary}
Description: {description}

Labels: {alert.labels}
Annotations: {alert.annotations}

Please analyze this Bank of Anthos service alert and provide:
1. Root cause analysis
2. Impact assessment  
3. Recommended remediation steps
4. Monitoring recommendations

Use your Bank of Anthos data collection tools to gather current metrics and logs for this service."""

        # Use the ADK /run endpoint with the persistent session
        payload = {
            "appName": ALERTMANAGER_APP_NAME,
            "userId": ALERTMANAGER_USER_ID,
            "sessionId": ALERTMANAGER_SESSION_ID,
            "newMessage": {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        }
        
        print(f"🔄 Processing alert: {alert_name} for service: {service}")
        print(f"📤 Sending to ADK endpoint with session: {ALERTMANAGER_SESSION_ID}")
        
        # 2 minute timeout allows for data collection and analysis
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post("http://localhost:8080/run", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Agent processed alert: {alert_name}")
                print(f"📋 Response preview: {str(result)[:200]}...")
                print(f"🌐 Full response available at: http://localhost:8080/apps/{ALERTMANAGER_APP_NAME}/users/{ALERTMANAGER_USER_ID}/sessions/{ALERTMANAGER_SESSION_ID}")
            else:
                print(f"❌ Agent error: {response.status_code} - {response.text}")
                
    except httpx.TimeoutException:
        print(f"⏰ Timeout processing alert: {alert.labels.get('alertname', 'Unknown')} - Agent may still be processing in background")
        print(f"💡 Check the ADK web interface at http://localhost:8080/ for the full response")
    except Exception as e:
        print(f"❌ Failed to process alert: {e}")
        print(f"Alert details: {alert}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


# --- Custom API Endpoints ---

@app.post("/alertmanager")
async def handle_alertmanager_webhook(payload: AlertmanagerWebhookPayload):
    """
    AlertManager webhook handler for Bank of Anthos alerts.
    Uses persistent session for background processing.
    """
    try:
        print(f"🚨 Received {len(payload.alerts)} alerts from AlertManager")
        
        # Process each alert using the persistent session
        for alert in payload.alerts:
            try:
                print(f"📋 Processing alert: {alert.labels}")
                
                if alert.status == "firing":
                    # Enhanced service detection for Bank of Anthos
                    service = alert.labels.get('service', '').lower()
                    deployment = alert.labels.get('deployment', '').lower()
                    pod = alert.labels.get('pod', '').lower()
                    instance = alert.labels.get('instance', '').lower()
                    
                    # Bank of Anthos service names (including database services)
                    bank_services = [
                        'frontend', 'userservice', 'contacts', 'balancereader', 'balance-reader',
                        'ledgerwriter', 'ledger-writer', 'transactionhistory', 'transaction-history',
                        'loadgenerator', 'load-generator', 'accounts-db', 'ledger-db'
                    ]
                    
                    # Check multiple fields for service identification
                    service_identified = False
                    detected_service = 'unknown'
                    
                    for field_value in [service, deployment, pod, instance]:
                        if field_value and any(svc in field_value for svc in bank_services):
                            service_identified = True
                            detected_service = field_value
                            break
                    
                    if service_identified:
                        print(f"🎯 Bank of Anthos alert detected for: {detected_service}")
                        # Process asynchronously in background to avoid webhook timeout
                        task = asyncio.create_task(send_alert_to_agent(alert))
                        print(f"🔄 Created async task for alert processing - processing in background")
                        task.add_done_callback(lambda t: print(f"✅ Background alert processing completed") if not t.exception() else print(f"❌ Background alert processing failed: {t.exception()}"))
                    else:
                        print(f"⏭️  Skipping non-Bank of Anthos service. Labels: {alert.labels}")
                else:
                    print(f"✅ Alert resolved: {alert.labels.get('alertname', 'Unknown')}")
                    
            except Exception as alert_error:
                print(f"❌ Error processing individual alert: {alert_error}")
                print(f"Alert data: {alert}")
                continue

        return {"status": "success", "message": f"Processed {len(payload.alerts)} alerts"}
        
    except Exception as e:
        print(f"❌ Failed to process webhook payload: {e}")
        print(f"Payload received: {payload}")
        return {"status": "error", "message": f"Failed to process alerts: {str(e)}"}


@app.get("/")
async def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"message": "ADK AlertManager Integration is running", "session": ALERTMANAGER_SESSION_ID}


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes readiness and liveness probes."""
    global session_created
    return {
        "status": "healthy", 
        "service": "adk-alertmanager-integration",
        "session_created": session_created,
        "session_id": ALERTMANAGER_SESSION_ID,
        "agent_name": AGENT_NAME
    }

@app.get("/status")
async def status_check():
    """Detailed status endpoint for debugging."""
    global session_created
    return {
        "alertmanager_integration": {
            "status": "running",
            "session_created": session_created,
            "session_id": ALERTMANAGER_SESSION_ID,
            "agent_name": AGENT_NAME,
            "endpoints": {
                "webhook": "/alertmanager",
                "web_ui": "/",
                "health": "/health",
                "status": "/status"
            }
        }
    }


# --- Main Execution Block ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on http://0.0.0.0:{port}")
    print("---------------------------------------------------------")
    print(f"-> ADK Agent Name: '{AGENT_NAME}'")
    print(f"-> Alertmanager Webhook: http://127.0.0.1:{port}/alertmanager")
    print(f"-> ADK Web Interface: http://127.0.0.1:{port}/")
    print(f"-> Health Check: http://127.0.0.1:{port}/health")
    print(f"-> Session ID: {ALERTMANAGER_SESSION_ID}")
    print("---------------------------------------------------------")
    uvicorn.run(app, host="0.0.0.0", port=port)
