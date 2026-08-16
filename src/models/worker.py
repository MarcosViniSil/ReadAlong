from dataclasses import dataclass
import datetime
from models.enum import  WorkerStatus

@dataclass
class Worker:
    id: str
    name: str
    status: WorkerStatus
    cpu_model: str
    cpu_cores: str
    cpu_threads: str
    ram_total: str
    ram_type: str
    ram_speed: str
    os: str
    os_version: str
    last_heart_beat: datetime
    created_at: datetime
    updated_at: datetime