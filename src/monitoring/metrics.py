import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import json
import os

@dataclass
class MetricPoint:
    """Individual metric point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class AlertMetrics:
    """Alert-specific metrics"""
    total_alerts: int = 0
    critical_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    investigated_alerts: int = 0
    avg_investigation_time: float = 0.0
    alerts_by_type: Dict[str, int] = field(default_factory=dict)
    
class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Start background cleanup
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start background thread for metric cleanup"""
        def cleanup():
            while True:
                time.sleep(3600)  # Run every hour
                self._cleanup_old_metrics()
                
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
        
    def _cleanup_old_metrics(self):
        """Remove old metrics"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self.lock:
            for metric_name, points in self.metrics.items():
                # Remove old points
                while points and points[0].timestamp < cutoff_time:
                    points.popleft()
                    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            
            # Also store as time series
            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                labels=labels or {}
            )
            self.metrics[name].append(point)
            
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            
            # Also store as time series
            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                labels=labels or {}
            )
            self.metrics[name].append(point)
            
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a value in a histogram"""
        with self.lock:
            self.histograms[name].append(value)
            
            # Keep only last 1000 values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
                
            # Also store as time series
            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                labels=labels or {}
            )
            self.metrics[name].append(point)
            
    def get_counter(self, name: str) -> float:
        """Get current counter value"""
        with self.lock:
            return self.counters.get(name, 0.0)
            
    def get_gauge(self, name: str) -> float:
        """Get current gauge value"""
        with self.lock:
            return self.gauges.get(name, 0.0)
            
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        with self.lock:
            values = self.histograms.get(name, [])
            
            if not values:
                return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}
                
            return {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p50": self._percentile(values, 50),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99)
            }
            
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
            
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
            
    def get_time_series(self, name: str, start_time: datetime = None, end_time: datetime = None) -> List[MetricPoint]:
        """Get time series data for a metric"""
        with self.lock:
            points = list(self.metrics.get(name, []))
            
            if start_time:
                points = [p for p in points if p.timestamp >= start_time]
                
            if end_time:
                points = [p for p in points if p.timestamp <= end_time]
                
            return points
            
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: self.get_histogram_stats(k) for k in self.histograms.keys()},
                "timestamp": datetime.now().isoformat()
            }

class SystemMetricsCollector:
    """Collects system metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.collecting = False
        
    def start_collection(self, interval: int = 60):
        """Start collecting system metrics"""
        self.collecting = True
        
        def collect():
            while self.collecting:
                try:
                    self._collect_system_metrics()
                except Exception as e:
                    print(f"Error collecting system metrics: {e}")
                    
                time.sleep(interval)
                
        thread = threading.Thread(target=collect, daemon=True)
        thread.start()
        
    def stop_collection(self):
        """Stop collecting system metrics"""
        self.collecting = False
        
    def _collect_system_metrics(self):
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.set_gauge("system.cpu.percent", cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics.set_gauge("system.memory.percent", memory.percent)
        self.metrics.set_gauge("system.memory.available_mb", memory.available / 1024 / 1024)
        self.metrics.set_gauge("system.memory.used_mb", memory.used / 1024 / 1024)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.metrics.set_gauge("system.disk.percent", disk.percent)
        self.metrics.set_gauge("system.disk.free_gb", disk.free / 1024 / 1024 / 1024)
        self.metrics.set_gauge("system.disk.used_gb", disk.used / 1024 / 1024 / 1024)
        
        # Process metrics
        process = psutil.Process()
        self.metrics.set_gauge("process.memory.rss_mb", process.memory_info().rss / 1024 / 1024)
        self.metrics.set_gauge("process.memory.vms_mb", process.memory_info().vms / 1024 / 1024)
        self.metrics.set_gauge("process.cpu.percent", process.cpu_percent())
        
        # Network metrics (if available)
        try:
            net_io = psutil.net_io_counters()
            self.metrics.set_gauge("system.network.bytes_sent", net_io.bytes_sent)
            self.metrics.set_gauge("system.network.bytes_recv", net_io.bytes_recv)
        except:
            pass

class ApplicationMetricsCollector:
    """Collects application-specific metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        
    def track_api_request(self, method: str, path: str, status_code: int, duration: float):
        """Track API request metrics"""
        labels = {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        }
        
        self.metrics.increment_counter("api.requests.total", 1.0, labels)
        self.metrics.observe_histogram("api.request.duration", duration, labels)
        
        # Track errors
        if status_code >= 400:
            self.metrics.increment_counter("api.errors.total", 1.0, labels)
            
    def track_database_query(self, query_type: str, table: str, duration: float, rows_affected: int = None):
        """Track database query metrics"""
        labels = {
            "query_type": query_type,
            "table": table
        }
        
        self.metrics.increment_counter("database.queries.total", 1.0, labels)
        self.metrics.observe_histogram("database.query.duration", duration, labels)
        
        if rows_affected is not None:
            self.metrics.observe_histogram("database.rows.affected", rows_affected, labels)
            
    def track_alert_created(self, rule_type: str, risk_score: int):
        """Track alert creation"""
        labels = {
            "rule_type": rule_type,
            "risk_level": self._get_risk_level(risk_score)
        }
        
        self.metrics.increment_counter("alerts.created.total", 1.0, labels)
        self.metrics.observe_histogram("alerts.risk_score", risk_score, labels)
        
    def track_alert_investigated(self, rule_type: str, investigation_time: float):
        """Track alert investigation"""
        labels = {"rule_type": rule_type}
        
        self.metrics.increment_counter("alerts.investigated.total", 1.0, labels)
        self.metrics.observe_histogram("alerts.investigation.duration", investigation_time, labels)
        
    def track_notification_sent(self, notification_type: str, success: bool):
        """Track notification sending"""
        labels = {
            "type": notification_type,
            "status": "success" if success else "failed"
        }
        
        self.metrics.increment_counter("notifications.sent.total", 1.0, labels)
        
    def track_data_ingestion(self, dataset_type: str, records_count: int, processing_time: float):
        """Track data ingestion"""
        labels = {"dataset_type": dataset_type}
        
        self.metrics.increment_counter("data.ingestion.total", 1.0, labels)
        self.metrics.observe_histogram("data.ingestion.records", records_count, labels)
        self.metrics.observe_histogram("data.ingestion.duration", processing_time, labels)
        
    def track_export_generated(self, export_type: str, records_count: int, generation_time: float):
        """Track export generation"""
        labels = {"export_type": export_type}
        
        self.metrics.increment_counter("exports.generated.total", 1.0, labels)
        self.metrics.observe_histogram("exports.records", records_count, labels)
        self.metrics.observe_histogram("exports.generation.duration", generation_time, labels)
        
    def track_user_action(self, action: str, user_role: str = None):
        """Track user actions"""
        labels = {"action": action}
        if user_role:
            labels["role"] = user_role
            
        self.metrics.increment_counter("user.actions.total", 1.0, labels)
        
    def _get_risk_level(self, risk_score: int) -> str:
        """Get risk level from score"""
        if risk_score >= 8:
            return "high"
        elif risk_score >= 5:
            return "medium"
        else:
            return "low"

class HealthChecker:
    """System health checker"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.health_checks = {}
        
    def register_health_check(self, name: str, check_func, critical: bool = False):
        """Register a health check"""
        self.health_checks[name] = {
            "func": check_func,
            "critical": critical
        }
        
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"
        
        for name, check_config in self.health_checks.items():
            try:
                start_time = time.time()
                result = check_config["func"]()
                duration = time.time() - start_time
                
                if result:
                    status = "healthy"
                    self.metrics.increment_counter("health.checks.passed", 1.0, {"check": name})
                else:
                    status = "unhealthy"
                    self.metrics.increment_counter("health.checks.failed", 1.0, {"check": name})
                    
                    if check_config["critical"]:
                        overall_status = "critical"
                    elif overall_status == "healthy":
                        overall_status = "degraded"
                        
                results[name] = {
                    "status": status,
                    "duration": duration,
                    "critical": check_config["critical"]
                }
                
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "critical": check_config["critical"]
                }
                
                self.metrics.increment_counter("health.checks.error", 1.0, {"check": name})
                
                if check_config["critical"]:
                    overall_status = "critical"
                elif overall_status == "healthy":
                    overall_status = "degraded"
                    
        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.now().isoformat()
        }

class MetricsExporter:
    """Exports metrics to various formats"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Export counters
        for name, value in self.metrics.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
            
        # Export gauges
        for name, value in self.metrics.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
            
        # Export histogram summaries
        for name, values in self.metrics.histograms.items():
            if values:
                stats = self.metrics.get_histogram_stats(name)
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_sum {stats['sum']}")
                lines.append(f"{name}_count {stats['count']}")
                
        return "\n".join(lines)
        
    def export_json(self) -> str:
        """Export metrics in JSON format"""
        return json.dumps(self.metrics.get_all_metrics(), indent=2)
        
    def export_csv(self, metric_name: str) -> str:
        """Export time series data in CSV format"""
        points = self.metrics.get_time_series(metric_name)
        
        if not points:
            return "timestamp,value\n"
            
        lines = ["timestamp,value"]
        for point in points:
            lines.append(f"{point.timestamp.isoformat()},{point.value}")
            
        return "\n".join(lines)

# Global metrics instances
metrics_collector = MetricsCollector()
system_metrics = SystemMetricsCollector(metrics_collector)
app_metrics = ApplicationMetricsCollector(metrics_collector)
health_checker = HealthChecker(metrics_collector)
metrics_exporter = MetricsExporter(metrics_collector)

# Convenience functions
def increment_counter(name: str, value: float = 1.0, labels: Dict[str, str] = None):
    """Increment a counter metric"""
    metrics_collector.increment_counter(name, value, labels)
    
def set_gauge(name: str, value: float, labels: Dict[str, str] = None):
    """Set a gauge metric"""
    metrics_collector.set_gauge(name, value, labels)
    
def observe_histogram(name: str, value: float, labels: Dict[str, str] = None):
    """Observe a value in a histogram"""
    metrics_collector.observe_histogram(name, value, labels)
    
def get_metrics_summary() -> Dict[str, Any]:
    """Get summary of all metrics"""
    return metrics_collector.get_all_metrics()

# Start system metrics collection
system_metrics.start_collection(interval=60)

# Register basic health checks
def check_disk_space():
    """Check if disk space is sufficient"""
    disk = psutil.disk_usage('/')
    return disk.percent < 90

def check_memory_usage():
    """Check if memory usage is reasonable"""
    memory = psutil.virtual_memory()
    return memory.percent < 85

def check_logs_directory():
    """Check if logs directory exists and is writable"""
    logs_dir = "logs"
    return os.path.exists(logs_dir) and os.access(logs_dir, os.W_OK)

health_checker.register_health_check("disk_space", check_disk_space, critical=True)
health_checker.register_health_check("memory_usage", check_memory_usage, critical=False)
health_checker.register_health_check("logs_directory", check_logs_directory, critical=True)