"""Tools for Bank of Anthos self-healing system."""

from .bank_of_anthos_ingestor import BankOfAnthosIngestorTool
from .kubernetes_action import KubernetesActionTool
from .alerting import AlertingTool
from .metrics import MetricsTool

# Create tool instances for easy access
ingestor = BankOfAnthosIngestorTool()
k8s_action = KubernetesActionTool() 
alerting = AlertingTool()
metrics = MetricsTool()

# Tool collections for agents (non-ADK versions for testing)
MONITORING_TOOLS = [ingestor, metrics]
ANALYSIS_TOOLS = [ingestor, metrics, alerting]
DECISION_TOOLS = [k8s_action, alerting]
TERMINATION_TOOLS = [ingestor, metrics]

__all__ = [
    'BankOfAnthosIngestorTool',
    'KubernetesActionTool', 
    'AlertingTool',
    'MetricsTool',
    'MONITORING_TOOLS',
    'ANALYSIS_TOOLS', 
    'DECISION_TOOLS',
    'TERMINATION_TOOLS'
]