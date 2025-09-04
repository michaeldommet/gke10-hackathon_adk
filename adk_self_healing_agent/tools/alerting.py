"""Alerting and notification tool with Slack integration."""

import logging
import os
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Alert severity levels for reference (use strings in function signatures)
VALID_SEVERITIES = ["low", "medium", "high", "critical"]

# Slack configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


class AlertingTool:
    """Tool for managing alerts and notifications with Slack integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emoji_map = {
            "low": "🟡",
            "medium": "🟠", 
            "high": "🔴",
            "critical": "🚨"
        }
        return emoji_map.get(severity, "⚪")
    
    def _get_severity_color(self, severity: str) -> str:
        """Get Slack color for severity level."""
        color_map = {
            "low": "#36a64f",      # Green
            "medium": "#ff9500",   # Orange  
            "high": "#ff0000",     # Red
            "critical": "#8B0000"  # Dark Red
        }
        return color_map.get(severity, "#808080")  # Gray default
    
    async def _send_slack_notification(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification to Slack webhook."""
        if not SLACK_WEBHOOK_URL:
            self.logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack notification")
            return {"status": "skipped", "reason": "webhook_url_not_configured"}
        
        try:
            emoji = self._get_severity_emoji(alert["severity"])
            color = self._get_severity_color(alert["severity"])
            
            # Create rich Slack message
            slack_payload = {
                "icon_emoji": ":robot_face:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} {alert['severity'].upper()} Alert - {alert['service']}",
                        "text": alert["message"],
                        "fields": [
                            {
                                "title": "Service",
                                "value": alert["service"],
                                "short": True
                            },
                            {
                                "title": "Severity", 
                                "value": alert["severity"].upper(),
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert["id"],
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert["timestamp"],
                                "short": True
                            }
                        ],
                        "footer": "ADK Self-Healing Agent",
                        "footer_icon": "https://example.com/adk-icon.png",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }
            
            # Add additional details if present
            if alert.get("details"):
                details_text = ""
                for key, value in alert["details"].items():
                    details_text += f"• *{key}*: {value}\n"
                
                if details_text:
                    slack_payload["attachments"][0]["fields"].append({
                        "title": "Additional Details",
                        "value": details_text,
                        "short": False
                    })
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SLACK_WEBHOOK_URL,
                    json=slack_payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Slack notification sent successfully for alert {alert['id']}")
                    return {"status": "sent", "platform": "slack", "response_code": response.status_code}
                else:
                    self.logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                    return {"status": "failed", "platform": "slack", "response_code": response.status_code, "error": response.text}
                    
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {str(e)}")
            return {"status": "error", "platform": "slack", "error": str(e)}
    
    async def send_alert(self, 
                        message: str, 
                        severity: str, 
                        service: str,
                        details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send an alert notification to Slack and store in history.
        
        Args:
            message: Alert message
            severity: Alert severity level (low, medium, high, critical)
            service: Service that triggered the alert
            details: Additional alert details
            
        Returns:
            Dictionary containing alert sending result
        """
        # Validate severity level
        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            severity = "medium"  # Default fallback
            
        self.logger.info(f"Sending {severity} alert for service {service}: {message}")
        
        alert = {
            "id": f"alert_{len(self.alert_history) + 1}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "message": message,
            "severity": severity,
            "service": service,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "processing"
        }
        
        # Send to Slack
        slack_result = await self._send_slack_notification(alert)
        alert["slack_result"] = slack_result
        
        # Update status based on Slack result
        if slack_result.get("status") == "sent":
            alert["status"] = "sent"
        elif slack_result.get("status") == "skipped":
            alert["status"] = "sent_fallback"  # Still consider it sent, just not to Slack
        else:
            alert["status"] = "failed"
        
        self.alert_history.append(alert)
        
        return alert
    
    async def create_incident(self, 
                             title: str, 
                             description: str, 
                             severity: str,
                             affected_services: List[str]) -> Dict[str, Any]:
        """
        Create an incident record.
        
        Args:
            title: Incident title
            description: Incident description
            severity: Incident severity (low, medium, high, critical)
            affected_services: List of affected services
            
        Returns:
            Dictionary containing incident creation result
        """
        # Validate severity level
        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            severity = "medium"  # Default fallback
            
        self.logger.info(f"Creating {severity} incident: {title}")
        
        incident = {
            "id": f"incident_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "description": description,
            "severity": severity,
            "affected_services": affected_services,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Implement actual incident management integration
        
        return incident
    
    async def get_alert_history(self, 
                               service: Optional[str] = None, 
                               severity: Optional[str] = None,
                               limit: int = 50) -> Dict[str, Any]:
        """
        Get alert history with optional filtering.
        
        Args:
            service: Filter by service name
            severity: Filter by severity level (low, medium, high, critical)
            limit: Maximum number of alerts to return
            
        Returns:
            Dictionary containing alert history
        """
        self.logger.info(f"Getting alert history (service: {service}, severity: {severity}, limit: {limit})")
        
        filtered_alerts = self.alert_history
        
        if service:
            filtered_alerts = [a for a in filtered_alerts if a.get("service") == service]
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.get("severity") == severity]
        
        # Sort by timestamp (most recent first) and limit
        filtered_alerts = sorted(filtered_alerts, 
                               key=lambda x: x.get("timestamp", ""), 
                               reverse=True)[:limit]
        
        return {
            "alerts": filtered_alerts,
            "count": len(filtered_alerts),
            "filters": {
                "service": service,
                "severity": severity,
                "limit": limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Dict[str, Any]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: Who acknowledged the alert
            
        Returns:
            Dictionary containing acknowledgment result
        """
        self.logger.info(f"Acknowledging alert {alert_id} by {acknowledged_by}")
        
        # Find and update the alert
        for alert in self.alert_history:
            if alert.get("id") == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = acknowledged_by
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                
                return {
                    "alert_id": alert_id,
                    "acknowledged": True,
                    "acknowledged_by": acknowledged_by,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        return {
            "alert_id": alert_id,
            "acknowledged": False,
            "error": "Alert not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_alert_rules(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check if metrics trigger any alert rules.
        
        Args:
            metrics: Service metrics to check against alert rules
            
        Returns:
            List of triggered alerts
        """
        self.logger.info("Checking alert rules against metrics")
        
        triggered_alerts = []
        
        # Define alert rules
        alert_rules = [
            {
                "name": "high_cpu_usage",
                "condition": lambda m: m.get("cpu_usage", 0) > 80,
                "severity": "high",
                "message": "High CPU usage detected"
            },
            {
                "name": "high_memory_usage", 
                "condition": lambda m: m.get("memory_usage", 0) > 85,
                "severity": "high",
                "message": "High memory usage detected"
            },
            {
                "name": "high_error_rate",
                "condition": lambda m: m.get("error_rate", 0) > 0.05,
                "severity": "critical",
                "message": "High error rate detected"
            },
            {
                "name": "pod_restarts",
                "condition": lambda m: m.get("pod_restarts", 0) > 3,
                "severity": "medium",
                "message": "Multiple pod restarts detected"
            }
        ]
        
        # Check each rule
        for rule in alert_rules:
            if rule["condition"](metrics):
                alert = {
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "service": metrics.get("service", "unknown"),
                    "triggered_at": datetime.utcnow().isoformat(),
                    "metrics": metrics
                }
                triggered_alerts.append(alert)
        
        return triggered_alerts
