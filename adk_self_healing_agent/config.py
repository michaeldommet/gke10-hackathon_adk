"""
Configuration settings for the ADK Self-Healing Agent.

This module provides configuration management for the agent,
including environment-specific settings, model configurations,
and operational parameters.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ModelConfig:
    """Configuration for Gemini model."""
    name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 8192
    top_p: float = 0.8
    top_k: int = 40

    @classmethod
    def from_env(cls) -> 'ModelConfig':
        """Create ModelConfig from environment variables."""
        return cls(
            name=os.getenv("ADK_MODEL_NAME", "gemini-2.5-flash"),
            temperature=float(os.getenv("ADK_MODEL_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("ADK_MODEL_MAX_TOKENS", "8192")),
            top_p=float(os.getenv("ADK_MODEL_TOP_P", "0.8")),
            top_k=int(os.getenv("ADK_MODEL_TOP_K", "40")),
        )


@dataclass
class MonitoringConfig:
    """Configuration for monitoring behavior."""
    interval_seconds: int = 60
    metrics_retention_hours: int = 24
    alert_cooldown_minutes: int = 15
    max_concurrent_remediations: int = 3


@dataclass
class KubernetesConfig:
    """Configuration for Kubernetes operations."""
    namespace: str = "bank-of-anthos"
    cluster_name: Optional[str] = None
    region: Optional[str] = None
    project_id: Optional[str] = None
    max_scale_factor: float = 3.0
    min_replicas: int = 1
    max_replicas: int = 10


@dataclass
class GoogleCloudConfig:
    """Configuration for Google Cloud integration."""
    project_id: Optional[str] = None
    region: str = "us-central1"
    vertex_ai_location: str = "us-central1"
    use_google_ai_studio: bool = False
    google_ai_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'GoogleCloudConfig':
        """Create GoogleCloudConfig from environment variables."""
        return cls(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            region=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"),
            vertex_ai_location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
            use_google_ai_studio=os.getenv("USE_GOOGLE_AI_STUDIO", "false").lower() == "true",
            google_ai_api_key=os.getenv("GOOGLE_AI_API_KEY"),
        )


@dataclass
class AlertingConfig:
    """Configuration for alerting and notifications."""
    slack_webhook_url: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    pagerduty_integration_key: Optional[str] = None
    enable_slack: bool = False
    enable_email: bool = False
    enable_pagerduty: bool = False


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_workload_identity: bool = True
    service_account: str = "self-healing-agent"
    required_permissions: Optional[List[str]] = None
    audit_logging: bool = True


@dataclass
class AutopilotConfig:
    """Simple autopilot configuration - either on or off."""
    enabled: bool = False
    
    def get_allowed_actions(self):
        """Get list of allowed tools based on autopilot configuration."""
        from adk_self_healing_agent.tools.adk_tools import (
            restart_deployment_tool,
            scale_deployment_tool,
            send_alert_tool,
        )
        
        # Always allow safe actions (Jira incident creation via MCP tools)
        allowed_tools = [send_alert_tool]
        
        # If autopilot is enabled, add destructive actions
        if self.enabled:
            allowed_tools.extend([restart_deployment_tool, scale_deployment_tool])
        
        return allowed_tools
    
    def get_status_summary(self) -> str:
        """Get human-readable status summary."""
        if self.enabled:
            return "Autopilot: ON (all actions enabled)"
        else:
            return "Autopilot: OFF (alerts + Jira incidents only)"
    
    def is_action_allowed(self, action_name: str) -> bool:
        """Check if a specific action is allowed."""
        # Safe actions are always allowed (Jira handled by MCP tools)
        if action_name in ["send_alert"]:
            return True
        
        # Destructive actions require autopilot to be enabled
        if action_name in ["restart_deployment", "scale_deployment"]:
            return self.enabled
        
        return False
class AgentConfig:
    """Main configuration class for the ADK Self-Healing Agent."""
    
    def __init__(self):
        # Initialize configurations
        self.model = ModelConfig.from_env()
        self.google_cloud = GoogleCloudConfig.from_env()
        self.monitoring = MonitoringConfig()
        self.kubernetes = KubernetesConfig()
        self.alerting = AlertingConfig()
        self.security = SecurityConfig()
        self.autopilot = AutopilotConfig()
        
        # Load environment-specific settings
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Monitoring configuration
        self.monitoring.interval_seconds = int(os.getenv("ADK_MONITORING_INTERVAL", self.monitoring.interval_seconds))
        self.monitoring.metrics_retention_hours = int(os.getenv("ADK_METRICS_RETENTION_HOURS", self.monitoring.metrics_retention_hours))
        self.monitoring.alert_cooldown_minutes = int(os.getenv("ADK_ALERT_COOLDOWN_MINUTES", self.monitoring.alert_cooldown_minutes))
        
        # Kubernetes configuration
        self.kubernetes.namespace = os.getenv("ADK_K8S_NAMESPACE", self.kubernetes.namespace)
        self.kubernetes.cluster_name = os.getenv("ADK_CLUSTER_NAME")
        self.kubernetes.region = os.getenv("ADK_REGION")
        self.kubernetes.project_id = os.getenv("ADK_PROJECT_ID")
        
        # Alerting configuration
        self.alerting.slack_webhook_url = os.getenv("ADK_SLACK_WEBHOOK_URL")
        self.alerting.email_recipients = os.getenv("ADK_EMAIL_RECIPIENTS", "").split(",") if os.getenv("ADK_EMAIL_RECIPIENTS") else []
        self.alerting.pagerduty_integration_key = os.getenv("ADK_PAGERDUTY_KEY")
        self.alerting.enable_slack = os.getenv("ADK_ENABLE_SLACK", "false").lower() == "true"
        self.alerting.enable_email = os.getenv("ADK_ENABLE_EMAIL", "false").lower() == "true"
        self.alerting.enable_pagerduty = os.getenv("ADK_ENABLE_PAGERDUTY", "false").lower() == "true"
        
        # Security configuration
        self.security.enable_workload_identity = os.getenv("ADK_ENABLE_WORKLOAD_IDENTITY", "true").lower() == "true"
        self.security.service_account = os.getenv("ADK_SERVICE_ACCOUNT", self.security.service_account)
        self.security.audit_logging = os.getenv("ADK_AUDIT_LOGGING", "true").lower() == "true"
        
        # Autopilot configuration - simple on/off mode
        self.autopilot.enabled = os.getenv("ADK_AUTOPILOT_MODE", "false").lower() == "true"
        
        # Backward compatibility with existing environment variables
        if os.getenv("AUTOPILOT_MODE", "").lower() == "true":
            self.autopilot.enabled = True
    
    @property
    def services_to_monitor(self) -> List[str]:
        """Get list of Bank of Anthos services to monitor."""
        return [
            "frontend",
            "userservice", 
            "contacts",
            "balancereader",
            "ledgerwriter",
            "transactionhistory",
            "loadgenerator"
        ]
    
    @property
    def service_dependencies(self) -> Dict[str, List[str]]:
        """Get service dependency mapping."""
        return {
            "frontend": ["userservice", "contacts", "balancereader", "transactionhistory"],
            "userservice": ["accounts-db"],
            "contacts": ["accounts-db"], 
            "balancereader": ["ledger-db"],
            "ledgerwriter": ["ledger-db"],
            "transactionhistory": ["ledger-db"],
            "loadgenerator": ["frontend"]
        }
    
    @property
    def anomaly_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get anomaly detection thresholds."""
        return {
            "cpu_usage": {
                "medium": 80.0,
                "high": 90.0,
                "critical": 95.0
            },
            "memory_usage": {
                "medium": 85.0,
                "high": 95.0,
                "critical": 98.0
            },
            "error_rate": {
                "medium": 0.05,  # 5%
                "high": 0.10,    # 10%
                "critical": 0.20  # 20%
            },
            "response_latency": {
                "medium": 1000.0,  # 1 second
                "high": 2000.0,    # 2 seconds
                "critical": 5000.0  # 5 seconds
            },
            "pod_restarts": {
                "medium": 3,
                "high": 5,
                "critical": 10
            }
        }
    
    def get_severity_for_threshold(self, metric_name: str, value: float) -> Severity:
        """Determine severity level for a metric value."""
        thresholds = self.anomaly_thresholds.get(metric_name, {})
        
        if value >= thresholds.get("critical", float('inf')):
            return Severity.CRITICAL
        elif value >= thresholds.get("high", float('inf')):
            return Severity.HIGH
        elif value >= thresholds.get("medium", float('inf')):
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            "model": {
                "name": self.model.name,
                "temperature": self.model.temperature,
                "max_tokens": self.model.max_tokens,
                "top_p": self.model.top_p,
                "top_k": self.model.top_k
            },
            "google_cloud": {
                "project_id": self.google_cloud.project_id,
                "region": self.google_cloud.region,
                "vertex_ai_location": self.google_cloud.vertex_ai_location,
                "use_google_ai_studio": self.google_cloud.use_google_ai_studio
            },
            "monitoring": {
                "interval_seconds": self.monitoring.interval_seconds,
                "metrics_retention_hours": self.monitoring.metrics_retention_hours,
                "alert_cooldown_minutes": self.monitoring.alert_cooldown_minutes,
                "max_concurrent_remediations": self.monitoring.max_concurrent_remediations
            },
            "kubernetes": {
                "namespace": self.kubernetes.namespace,
                "cluster_name": self.kubernetes.cluster_name,
                "region": self.kubernetes.region,
                "project_id": self.kubernetes.project_id,
                "max_scale_factor": self.kubernetes.max_scale_factor,
                "min_replicas": self.kubernetes.min_replicas,
                "max_replicas": self.kubernetes.max_replicas
            },
            "alerting": {
                "enable_slack": self.alerting.enable_slack,
                "enable_email": self.alerting.enable_email,
                "enable_pagerduty": self.alerting.enable_pagerduty
            },
            "security": {
                "enable_workload_identity": self.security.enable_workload_identity,
                "service_account": self.security.service_account,
                "audit_logging": self.security.audit_logging
            },
            "autopilot": {
                "enabled": self.autopilot.enabled
            }
        }


# Global configuration instance
_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Get the global agent configuration."""
    global _config
    if _config is None:
        _config = AgentConfig()
    return _config


def set_autopilot_mode(enabled: bool) -> None:
    """Dynamically enable/disable autopilot mode."""
    config = get_config()
    config.autopilot.enabled = enabled


def get_autopilot_status() -> str:
    """Get current autopilot status summary."""
    config = get_config()
    return config.autopilot.get_status_summary()


# Export key classes and functions
__all__ = [
    "Severity",
    "AutopilotConfig",
    "ModelConfig",
    "GoogleCloudConfig",
    "MonitoringConfig",
    "KubernetesConfig",
    "AlertingConfig",
    "SecurityConfig",
    "AgentConfig",
    "get_config",
    "set_autopilot_mode",
    "get_autopilot_status",
]