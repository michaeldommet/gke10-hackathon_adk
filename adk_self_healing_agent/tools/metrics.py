
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Metrics collection and analysis tool."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics

logger = logging.getLogger(__name__)


class MetricsTool:
    """Tool for collecting and analyzing metrics from Bank of Anthos services."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_cache = {}
    
    async def collect_service_metrics(self, 
                                    service_name: str, 
                                    time_range: str = "5m",
                                    metrics_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Collect comprehensive metrics for a service.
        
        Args:
            service_name: Name of the service
            time_range: Time range for metrics collection
            metrics_list: Specific metrics to collect (if None, collect all)
            
        Returns:
            Dictionary containing collected metrics
        """
        self.logger.info(f"Collecting metrics for service: {service_name}")
        
        # Default metrics to collect
        if metrics_list is None:
            metrics_list = [
                "cpu_usage", "memory_usage", "request_rate", "error_rate", 
                "response_latency", "pod_count", "restart_count"
            ]
        
        # TODO: Implement actual metrics collection from Cloud Monitoring
        metrics = {
            "service": service_name,
            "time_range": time_range,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }
        
        # Mock metrics data based on service
        base_values = {
            "frontend": {"cpu": 45, "memory": 60, "error_rate": 0.02},
            "userservice": {"cpu": 30, "memory": 40, "error_rate": 0.01},
            "balancereader": {"cpu": 25, "memory": 35, "error_rate": 0.005},
            "default": {"cpu": 20, "memory": 30, "error_rate": 0.001}
        }
        
        base = base_values.get(service_name, base_values["default"])
        
        for metric in metrics_list:
            if metric == "cpu_usage":
                metrics["metrics"][metric] = base["cpu"]
            elif metric == "memory_usage":
                metrics["metrics"][metric] = base["memory"]
            elif metric == "request_rate":
                metrics["metrics"][metric] = 150.0  # requests per second
            elif metric == "error_rate":
                metrics["metrics"][metric] = base["error_rate"]
            elif metric == "response_latency":
                metrics["metrics"][metric] = 120.5  # milliseconds
            elif metric == "pod_count":
                metrics["metrics"][metric] = 2
            elif metric == "restart_count":
                metrics["metrics"][metric] = 0
        
        # Cache the metrics
        self.metrics_cache[f"{service_name}_{time_range}"] = metrics
        
        return metrics
    
    async def analyze_metric_trends(self, 
                                  service_name: str, 
                                  metric_name: str,
                                  time_range: str = "1h") -> Dict[str, Any]:
        """
        Analyze trends for a specific metric over time.
        
        Args:
            service_name: Name of the service
            metric_name: Name of the metric to analyze
            time_range: Time range for trend analysis
            
        Returns:
            Dictionary containing trend analysis
        """
        self.logger.info(f"Analyzing trends for {metric_name} in service {service_name}")
        
        # TODO: Implement actual trend analysis with historical data
        # For now, generate mock trend data
        
        # Generate mock historical data points
        data_points = []
        current_time = datetime.utcnow()
        
        for i in range(12):  # 12 data points over time range
            timestamp = current_time - timedelta(minutes=i * 5)
            # Add some variance to simulate real data
            base_value = 45.0 if metric_name == "cpu_usage" else 0.02
            variance = base_value * 0.1 * (0.5 - (i % 3) / 6)  # Some pattern
            value = base_value + variance
            
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": round(value, 3)
            })
        
        # Calculate trend statistics
        values = [dp["value"] for dp in data_points]
        
        analysis = {
            "service": service_name,
            "metric": metric_name,
            "time_range": time_range,
            "data_points": data_points,
            "statistics": {
                "mean": round(statistics.mean(values), 3),
                "median": round(statistics.median(values), 3),
                "min": min(values),
                "max": max(values),
                "std_dev": round(statistics.stdev(values), 3) if len(values) > 1 else 0
            },
            "trend": "stable",  # could be "increasing", "decreasing", "stable"
            "anomalies_detected": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Simple trend detection
        if len(values) >= 3:
            recent_avg = statistics.mean(values[:3])
            older_avg = statistics.mean(values[-3:])
            
            if recent_avg > older_avg * 1.1:
                analysis["trend"] = "increasing"
            elif recent_avg < older_avg * 0.9:
                analysis["trend"] = "decreasing"
        
        return analysis
    
    async def compare_services_metrics(self, 
                                     services: List[str], 
                                     metric_name: str,
                                     time_range: str = "5m") -> Dict[str, Any]:
        """
        Compare a specific metric across multiple services.
        
        Args:
            services: List of service names to compare
            metric_name: Name of the metric to compare
            time_range: Time range for comparison
            
        Returns:
            Dictionary containing service comparison
        """
        self.logger.info(f"Comparing {metric_name} across services: {services}")
        
        comparison = {
            "metric": metric_name,
            "time_range": time_range,
            "services": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Collect metrics for each service
        for service in services:
            metrics = await self.collect_service_metrics(service, time_range, [metric_name])
            comparison["services"][service] = metrics["metrics"].get(metric_name, 0)
        
        # Calculate comparison statistics
        values = list(comparison["services"].values())
        if values:
            comparison["statistics"] = {
                "average": round(statistics.mean(values), 3),
                "min_service": min(comparison["services"], key=comparison["services"].get),
                "max_service": max(comparison["services"], key=comparison["services"].get),
                "range": round(max(values) - min(values), 3)
            }
        
        return comparison
    
    async def detect_anomalies(self, 
                             service_name: str, 
                             threshold_multiplier: float = 2.0) -> Dict[str, Any]:
        """
        Detect anomalies in service metrics.
        
        Args:
            service_name: Name of the service to check
            threshold_multiplier: Multiplier for standard deviation threshold
            
        Returns:
            Dictionary containing anomaly detection results
        """
        self.logger.info(f"Detecting anomalies for service: {service_name}")
        
        # Get current metrics
        current_metrics = await self.collect_service_metrics(service_name)
        
        # TODO: Implement proper anomaly detection with historical baseline
        anomalies = {
            "service": service_name,
            "threshold_multiplier": threshold_multiplier,
            "anomalies_detected": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Simple threshold-based anomaly detection
        thresholds = {
            "cpu_usage": 80,
            "memory_usage": 85,
            "error_rate": 0.05,
            "response_latency": 1000
        }
        
        for metric, value in current_metrics["metrics"].items():
            threshold = thresholds.get(metric)
            if threshold and value > threshold:
                anomalies["anomalies_detected"].append({
                    "metric": metric,
                    "current_value": value,
                    "threshold": threshold,
                    "severity": "high" if value > threshold * 1.5 else "medium"
                })
        
        return anomalies
    
    async def get_health_score(self, service_name: str) -> Dict[str, Any]:
        """
        Calculate an overall health score for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Dictionary containing health score and components
        """
        self.logger.info(f"Calculating health score for service: {service_name}")
        
        # Get current metrics
        metrics = await self.collect_service_metrics(service_name)
        
        # Calculate component scores (0-100)
        scores = {}
        
        # CPU health (100 = 0% usage, 0 = 100% usage)
        cpu_usage = metrics["metrics"].get("cpu_usage", 0)
        scores["cpu"] = max(0, 100 - cpu_usage)
        
        # Memory health
        memory_usage = metrics["metrics"].get("memory_usage", 0)
        scores["memory"] = max(0, 100 - memory_usage)
        
        # Error rate health (100 = 0% errors, 0 = 10%+ errors)
        error_rate = metrics["metrics"].get("error_rate", 0)
        scores["errors"] = max(0, 100 - (error_rate * 1000))  # Scale for visibility
        
        # Latency health (100 = <100ms, 0 = >1000ms)
        latency = metrics["metrics"].get("response_latency", 100)
        scores["latency"] = max(0, 100 - ((latency - 100) / 9))  # Linear scale
        
        # Stability health (based on restarts)
        restart_count = metrics["metrics"].get("restart_count", 0)
        scores["stability"] = max(0, 100 - (restart_count * 20))
        
        # Calculate overall health score (weighted average)
        weights = {"cpu": 0.2, "memory": 0.2, "errors": 0.3, "latency": 0.2, "stability": 0.1}
        overall_score = sum(scores[component] * weights[component] for component in scores)
        
        # Determine health status
        if overall_score >= 80:
            status = "healthy"
        elif overall_score >= 60:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "service": service_name,
            "overall_score": round(overall_score, 1),
            "status": status,
            "component_scores": scores,
            "weights": weights,
            "timestamp": datetime.utcnow().isoformat()
        }
