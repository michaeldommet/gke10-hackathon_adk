"""
ADK Self-Healing Agent for Bank of Anthos.

This package provides an autonomous self-healing agent built with Google's
Agent Development Kit (ADK) for monitoring and remediating issues in the
Bank of Anthos microservices application.

Key Components:
- SelfHealingRootAgent: Main orchestration agent
- ADK Tools: Bank of Anthos integration tools
- Structured Outputs: Pydantic models for agent communication
"""

__version__ = "1.0.0"

# Only import non-ADK dependent components by default
from .tools import (
    BankOfAnthosIngestorTool,
    KubernetesActionTool,
    AlertingTool,
    MetricsTool
)

# ADK-dependent imports are available but not imported by default
# Use: from adk_self_healing_agent.agent import SelfHealingRootAgent
# when ADK is available

__all__ = [
    'BankOfAnthosIngestorTool',
    'KubernetesActionTool', 
    'AlertingTool',
    'MetricsTool'
]
