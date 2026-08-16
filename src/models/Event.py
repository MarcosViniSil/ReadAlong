from dataclasses import dataclass
import datetime

from models.enum import EventType

@dataclass
class WorkerMetric:
    id: str
    event_type: EventType
    occurred_at: datetime
    entity_type: str
    entity_id: float
    actor_type: float
    processing_run_id: str
    correlation_id: str
    causation_id: str
    payload: str   