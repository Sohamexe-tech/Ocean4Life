"""
OceanShield AI - Report Processing Pipeline

Coordinates the complete workflow:
Report → Classification → Severity → Credibility → Geocoding → Incident
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Tuple, Optional
from geopy.geocoders import Nominatim

from models.ocean_models import OceanReport, OceanIncident
from services.classifier import safe_classify
from services.severity_assessor import assess_severity
from services.credibility_scorer import CredibilityScorer
from config import OCEAN_HAZARD_TYPES


class ReportProcessor:
    """Process citizen hazard reports through the complete pipeline."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="oceanshield_ai")
        self.credibility_scorer = CredibilityScorer()
    
    def create_report_id(self) -> str:
        """Generate a unique report ID (OS-RPT-XXXXXX)"""
        unique = str(uuid.uuid4())[:6].upper()
        return f"OS-RPT-{unique}"
    
    def process_citizen_report(
        self,
        description: str,
        location: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reporter_name: Optional[str] = None,
        is_demo: bool = False
    ) -> Tuple[OceanReport, Dict]:
        """
        Process a citizen hazard report through the complete pipeline.
        
        Returns:
            (report, metadata)
            report: OceanReport object with all fields filled
            metadata: Processing details and reasoning
        """
        
        metadata = {
            "steps": [],
            "errors": [],
            "warnings": [],
        }
        
        # Step 1: Create report object
        report_id = self.create_report_id()
        report = OceanReport(
            report_id=report_id,
            description=description,
            location=location,
            timestamp=datetime.now().isoformat(),
            source="citizen_report",
            reporter_name=reporter_name,
            is_demo=is_demo,
            status="ANALYZING"
        )
        metadata["steps"].append(f"Report created: {report_id}")
        
        # Step 2: Handle location/coordinates
        report.latitude = latitude
        report.longitude = longitude
        
        if latitude and longitude:
            report.location_type = "USER_PROVIDED"
            metadata["steps"].append(f"User-provided coordinates: ({latitude}, {longitude})")
        else:
            # Try geocoding
            geocoded = self._geocode_location(location)
            if geocoded:
                report.latitude, report.longitude, report.location_type = geocoded
                metadata["steps"].append(f"Geocoded location: ({report.latitude}, {report.longitude})")
            else:
                report.location_type = "USER_PROVIDED"
                metadata["steps"].append(f"Geocoding failed, using location text: {location}")
        
        # Step 3: Classify hazard
        classification = safe_classify(description, location)
        report.raw_hazard_type = classification.get("hazard_type", "OTHER")
        report.hazard_type = report.raw_hazard_type
        report.hazard_confidence = classification.get("confidence", 0.5)
        
        metadata["steps"].append(
            f"Classification: {report.hazard_type} (confidence: {report.hazard_confidence:.2f})"
        )
        
        # Step 4: Assess severity
        evidence = classification.get("evidence", [])
        severity, severity_evidence = assess_severity(
            report.hazard_type,
            description,
            evidence,
            report_count=1
        )
        
        metadata["steps"].append(f"Severity assessment: {severity}")
        metadata["severity_evidence"] = severity_evidence
        
        # Step 5: Score credibility
        score, factors = self.credibility_scorer.score_report(report)
        metadata["credibility_score"] = score
        metadata["credibility_factors"] = factors
        metadata["steps"].append(f"Credibility score: {score}/100")
        
        # Mark as classified
        report.status = "CLASSIFIED"
        metadata["steps"].append("Report processing complete")
        
        return report, metadata
    
    def _geocode_location(self, location: str) -> Optional[Tuple[float, float, str]]:
        """
        Geocode a location string to coordinates.
        
        Returns:
            (latitude, longitude, source_type) or None
        """
        
        if not location or len(location.strip()) < 2:
            return None
        
        try:
            geo = self.geolocator.geocode(location, timeout=5)
            if geo:
                return (geo.latitude, geo.longitude, "GEOCODED")
        except Exception as e:
            pass
        
        return None
    
    def cluster_into_incident(
        self,
        reports: list,  # List of OceanReport objects
        incident_id: Optional[str] = None
    ) -> OceanIncident:
        """
        Cluster multiple reports into a single incident.
        
        Returns:
            OceanIncident object
        """
        
        if not reports:
            raise ValueError("Cannot create incident without reports")
        
        # Generate incident ID if not provided
        if not incident_id:
            unique = str(uuid.uuid4())[:6].upper()
            incident_id = f"OS-INC-{unique}"
        
        # All reports should have same hazard type (verified before clustering)
        hazard_type = reports[0].hazard_type or "OTHER"
        
        # Aggregate location (use first report with coordinates)
        latitude = None
        longitude = None
        location = reports[0].location
        
        for report in reports:
            if report.latitude and report.longitude:
                latitude = report.latitude
                longitude = report.longitude
                break
        
        # Aggregate evidence
        evidence = []
        for report in reports:
            if report.description:
                evidence.extend(report.description.split()[:5])  # First 5 words
        
        evidence = list(set(evidence))[:10]  # Unique, top 10
        
        # Create incident
        incident = OceanIncident(
            incident_id=incident_id,
            hazard_type=hazard_type,
            location=location,
            latitude=latitude,
            longitude=longitude,
            severity="PENDING",
            ai_credibility_score=50,
            credibility_level="MODERATE",
            report_count=len(reports),
            report_ids=[r.report_id for r in reports],
            reports=reports,
            evidence=evidence,
            status="PENDING"
        )
        
        # Score the incident
        score, factors, level = self.credibility_scorer.score_incident(incident)
        incident.ai_credibility_score = score
        incident.credibility_level = level
        incident.credibility_factors = factors
        
        return incident


def process_citizen_report(
    description: str,
    location: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    reporter_name: Optional[str] = None,
    is_demo: bool = False
) -> Tuple[OceanReport, Dict]:
    """
    Quick function to process a citizen report.
    """
    processor = ReportProcessor()
    return processor.process_citizen_report(
        description,
        location,
        latitude,
        longitude,
        reporter_name,
        is_demo
    )
