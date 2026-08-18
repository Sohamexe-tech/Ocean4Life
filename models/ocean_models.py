"""
OceanShield AI - Report and Incident Models

Separates citizen reports from verified incidents.
Multiple reports can be clustered into a single incident.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OceanReport(BaseModel):
    """Represents a single ocean hazard report from any source"""
    report_id: str
    description: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_type: Optional[str] = None  # USER_PROVIDED, GEOCODED, AI_INFERRED
    timestamp: str
    source: str  # citizen_report, news, social_media, etc.
    reporter_name: Optional[str] = None
    
    # AI Classification (filled after processing)
    raw_hazard_type: Optional[str] = None  # Raw LLM classification
    hazard_type: Optional[str] = None  # Final hazard type (COASTAL_FLOODING, etc)
    hazard_confidence: Optional[float] = None  # 0-1 confidence in classification
    
    # Status tracking
    status: str = "PENDING"  # PENDING, ANALYZING, CLASSIFIED, FAILED
    error_message: Optional[str] = None
    
    # Metadata
    is_demo: bool = False
    

class OceanIncident(BaseModel):
    """Represents a deduplicated, verified ocean hazard incident"""
    incident_id: str
    hazard_type: str  # COASTAL_FLOODING, STORM_SURGE, etc.
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Severity and credibility
    severity: str  # LOW, MODERATE, HIGH, CRITICAL
    ai_credibility_score: int  # 0-100
    credibility_level: str  # LOW, MODERATE, HIGH, VERY_HIGH
    
    # Report clustering
    report_count: int = 1
    report_ids: List[str] = Field(default_factory=list)  # Linked report IDs
    reports: List[OceanReport] = Field(default_factory=list)  # Embedded reports
    
    # Evidence and reasoning
    evidence: List[str] = Field(default_factory=list)  # Supporting keywords/phrases
    severity_evidence: List[str] = Field(default_factory=list)  # Why it's this severity
    credibility_factors: dict = Field(default_factory=dict)  # Credibility breakdown
    
    # Status and timestamps
    status: str = "PENDING"  # PENDING, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Metadata
    is_demo: bool = False


class Need(BaseModel):
    """Legacy model - maintained for backward compatibility"""
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    source: str
    timestamp: str
    hazard_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_type: Optional[str] = None


class UniqueIncident(BaseModel):
    """Legacy model - maintained for backward compatibility"""
    incident_id: str
    need_type: str
    location: Optional[str] = None
    urgency: int
    summary: str
    report_count: int = 1
    sources: List[str] = Field(default_factory=list)
    original_reports: List[Need] = Field(default_factory=list)
    confidence_score: float = 0.0
    hazard_type: Optional[str] = None
    severity: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ai_confidence: Optional[float] = None
    evidence: List[str] = Field(default_factory=list)
    status: Optional[str] = "PENDING"
