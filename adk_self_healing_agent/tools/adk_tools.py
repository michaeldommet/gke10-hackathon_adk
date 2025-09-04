"""ADK Function Tools for Bank of Anthos Self-Healing Agent."""

from typing import Optional
from google.adk.tools import FunctionTool, ToolContext
from .bank_of_anthos_ingestor import BankOfAnthosIngestorTool
from .kubernetes_action import KubernetesActionTool
from .alerting import AlertingTool
from .metrics import MetricsTool

# Initialize tool instances
ingestor = BankOfAnthosIngestorTool()
k8s_action = KubernetesActionTool()
alerting = AlertingTool()
metrics = MetricsTool()

# Tool wrapper functions with proper signatures

async def get_service_metrics(service_name: str, time_range: str = "5m", tool_context: Optional[ToolContext] = None):
    """Collect metrics for a specific Bank of Anthos service.
    
    Args:
        service_name: Name of the service (e.g., 'frontend', 'userservice')
        time_range: Time range for metrics (e.g., '5m', '1h')
        tool_context: The ADK tool context
        
    Returns:
        Service metrics data
    """
    return await ingestor.get_service_metrics(service_name, time_range)

async def get_service_logs(service_name: str, level: str = "ERROR", time_range: str = "5m", tool_context: Optional[ToolContext] = None):
    """Collect logs for a specific Bank of Anthos service.
    
    Args:
        service_name: Name of the service
        level: Log level filter (ERROR, WARN, INFO, DEBUG)
        time_range: Time range for logs
        tool_context: The ADK tool context
        
    Returns:
        Service logs data
    """
    return await ingestor.get_service_logs(service_name, level, time_range)

async def get_pod_status(namespace: str = "default", service_name: Optional[str] = None, tool_context: Optional[ToolContext] = None):
    """Get Kubernetes pod status for Bank of Anthos services.
    
    Args:
        namespace: Kubernetes namespace
        service_name: Optional specific service name filter
        tool_context: The ADK tool context
        
    Returns:
        Pod status information
    """
    return await ingestor.get_pod_status(namespace, service_name)

async def restart_deployment(deployment_name: str, namespace: str = "default", tool_context: Optional[ToolContext] = None):
    """Restart a Kubernetes deployment.
    
    Args:
        deployment_name: Name of the deployment to restart
        namespace: Kubernetes namespace
        tool_context: The ADK tool context
        
    Returns:
        Restart operation result
    """
    return await k8s_action.restart_deployment(deployment_name, namespace)

async def scale_deployment(deployment_name: str, replicas: int, namespace: str = "default", tool_context: Optional[ToolContext] = None):
    """Scale a Kubernetes deployment.
    
    Args:
        deployment_name: Name of the deployment to scale
        replicas: Target number of replicas
        namespace: Kubernetes namespace
        tool_context: The ADK tool context
        
    Returns:
        Scaling operation result
    """
    return await k8s_action.scale_deployment(deployment_name, replicas, namespace)

async def send_alert(message: str, severity: str = "medium", 
               service_name: Optional[str] = None, tool_context: Optional[ToolContext] = None):
    """Send an alert notification.
    
    Args:
        message: Alert message
        severity: Alert severity level (low, medium, high, critical)
        service_name: Optional service name for context
        tool_context: The ADK tool context
        
    Returns:
        Alert sending result
    """
    service = service_name or "unknown"
    return await alerting.send_alert(message, severity, service)

# Note: create_incident functionality moved to Jira MCP tools
# Use createJiraIssue in project "SUP" for incident management

# Create FunctionTool instances with only the func parameter
get_service_metrics_tool = FunctionTool(func=get_service_metrics)
get_service_logs_tool = FunctionTool(func=get_service_logs)
get_pod_status_tool = FunctionTool(func=get_pod_status)
restart_deployment_tool = FunctionTool(func=restart_deployment)
scale_deployment_tool = FunctionTool(func=scale_deployment)
send_alert_tool = FunctionTool(func=send_alert)
# create_incident_tool removed - use Jira MCP tools instead

# Export all tools
all_tools = [
    get_service_metrics_tool,
    get_service_logs_tool,
    get_pod_status_tool,
    restart_deployment_tool,
    scale_deployment_tool,
    send_alert_tool,
    # create_incident_tool removed
]
