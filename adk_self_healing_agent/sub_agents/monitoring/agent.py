"""Monitoring agent for Bank of Anthos services."""

from google.adk.agents import Agent

from adk_self_healing_agent.sub_agents.monitoring.prompt import MONITORING_AGENT_PROMPT
from adk_self_healing_agent.config import get_config
from adk_self_healing_agent.tools.adk_tools import (
    get_service_metrics_tool,
    get_service_logs_tool,
    get_pod_status_tool,
)

config = get_config()

monitoring_agent = Agent(
    model=config.model.name,
    name="monitoring_agent",
    description="Monitors Bank of Anthos services and detects anomalies",
    instruction=MONITORING_AGENT_PROMPT,
    tools=[
        get_service_metrics_tool,
        get_service_logs_tool,
        get_pod_status_tool,
    ],
)
