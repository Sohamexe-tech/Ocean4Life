from pydantic import BaseModel
from typing import List, Optional


class Need(BaseModel):
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    source: str
    timestamp: str


class UniqueIncident(BaseModel):
    incident_id: str
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    report_count: int = 1
    sources: List[str] = []
    original_reports: List[Need] = []
    confidence_score: float = 0.0