from dataclasses import dataclass
import datetime

@dataclass
class WorkerMetric:
    id: str
    worker_id: str
    timestamp: datetime
    cpu_usage: str
    memory_usage: str
    disk_usage: str
    cpu_temperature: str