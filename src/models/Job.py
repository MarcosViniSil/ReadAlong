from dataclasses import dataclass
import datetime
from models.enum import BookStatus, JobType

@dataclass
class Job:
    id: str
    processing_run_id: str
    page_id: str
    chunk_id: str
    type: JobType
    status: BookStatus
    worker_id : str
    attempt: int
    queued_at: datetime
    started_at: datetime
    finished_at: datetime
    error_code: int
    error_message: str