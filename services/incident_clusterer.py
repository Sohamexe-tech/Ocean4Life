"""
OceanShield AI - Report to Incident Clustering Service

Deduplicates and clusters citizen reports into incidents.
Reuses existing DBSCAN semantic deduplication logic.
"""

from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models.ocean_models import OceanReport, OceanIncident
from services.report_processor import ReportProcessor
from services.data_store import get_data_store


class IncidentClusterer:
    """Cluster reports into incidents using semantic deduplication."""
    
    def __init__(self, text_similarity_threshold: float = 0.75, location_threshold_km: float = 5.0):
        self.text_similarity_threshold = text_similarity_threshold
        self.location_threshold_km = location_threshold_km
        self.processor = ReportProcessor()
        self.data_store = get_data_store()
    
    def cluster_reports(self, reports: List[OceanReport]) -> List[OceanIncident]:
        """
        Cluster multiple reports into incidents.
        
        Uses text similarity and location proximity to group reports.
        Returns list of OceanIncident objects.
        """
        
        if not reports:
            return []
        
        if len(reports) == 1:
            # Single report becomes an incident
            incident = self.processor.cluster_into_incident([reports[0]])
            return [incident]
        
        # Compute text similarity matrix
        try:
            descriptions = [r.description for r in reports]
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(descriptions).toarray()
            
            # DBSCAN clustering on text similarity
            clustering = DBSCAN(
                eps=1 - self.text_similarity_threshold,
                min_samples=1,
                metric='cosine'
            ).fit(tfidf_matrix)
            
            # Group reports by cluster
            clusters = {}
            for idx, label in enumerate(clustering.labels_):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(reports[idx])
            
            # Create incidents from clusters
            incidents = []
            for cluster_reports in clusters.values():
                # Verify all reports in cluster have same hazard type
                hazard_types = set(r.hazard_type for r in cluster_reports if r.hazard_type)
                
                if len(hazard_types) > 1:
                    # Different hazard types - may need to split
                    # For now, use most common hazard type
                    from collections import Counter
                    hazard_type = Counter(hazard_types).most_common(1)[0][0]
                    # Filter to same hazard type
                    cluster_reports = [r for r in cluster_reports if r.hazard_type == hazard_type]
                
                if cluster_reports:
                    incident = self.processor.cluster_into_incident(cluster_reports)
                    incidents.append(incident)
            
            return incidents
        
        except Exception as e:
            print(f"Error clustering reports: {e}")
            # Fallback: one report per incident
            return [self.processor.cluster_into_incident([r]) for r in reports]
    
    def cluster_with_existing(self, new_reports: List[OceanReport]) -> Tuple[List[OceanIncident], Dict]:
        """
        Cluster new reports with existing incidents.
        
        Attempts to merge new reports into existing incidents if similar.
        Creates new incidents for dissimilar reports.
        
        Returns:
            (incidents, metadata)
            incidents: List of new/updated incidents
            metadata: Clustering details
        """
        
        metadata = {
            "new_incidents": 0,
            "updated_incidents": 0,
            "merged_reports": 0,
        }
        
        if not new_reports:
            return [], metadata
        
        existing_incidents = self.data_store.get_all_incidents()
        incidents_to_save = []
        
        for report in new_reports:
            # Try to find matching incident
            matched = False
            
            for incident in existing_incidents:
                # Check if report should be merged into this incident
                if self._should_merge(report, incident):
                    # Add report to incident
                    incident.reports.append(report)
                    incident.report_ids.append(report.report_id)
                    incident.report_count = len(incident.reports)
                    
                    # Re-compute severity and credibility
                    from services.severity_assessor import assess_incident_severity
                    from services.credibility_scorer import CredibilityScorer
                    
                    severity, _ = assess_incident_severity(incident)
                    incident.severity = severity
                    
                    scorer = CredibilityScorer()
                    score, factors, level = scorer.score_incident(incident)
                    incident.ai_credibility_score = score
                    incident.credibility_level = level
                    
                    incident.last_updated = datetime.now().isoformat()
                    
                    incidents_to_save.append(incident)
                    metadata["merged_reports"] += 1
                    metadata["updated_incidents"] += 1
                    matched = True
                    break
            
            if not matched:
                # Create new incident for this report
                incident = self.processor.cluster_into_incident([report])
                incidents_to_save.append(incident)
                metadata["new_incidents"] += 1
        
        # Save incidents
        for incident in incidents_to_save:
            self.data_store.save_incident(incident)
        
        return incidents_to_save, metadata
    
    def _should_merge(self, report: OceanReport, incident: OceanIncident) -> bool:
        """
        Determine if a report should be merged into an incident.
        
        Criteria:
        1. Same hazard type
        2. Similar location (within threshold)
        3. Similar description (text similarity)
        4. Recent timeframe (within 24 hours)
        """
        
        # Check hazard type
        if report.hazard_type != incident.hazard_type:
            return False
        
        # Check location similarity
        if not self._check_location_similarity(report, incident):
            return False
        
        # Check text similarity with incident summary/evidence
        incident_text = " ".join(incident.evidence) + " " + incident.reports[0].description
        similarity = self._text_similarity(report.description, incident_text)
        
        if similarity < self.text_similarity_threshold:
            return False
        
        # Check temporal proximity (within 24 hours)
        from datetime import datetime, timedelta
        try:
            report_time = datetime.fromisoformat(report.timestamp)
            incident_time = datetime.fromisoformat(incident.last_updated)
            time_diff = abs((report_time - incident_time).total_seconds())
            if time_diff > 86400:  # 24 hours
                return False
        except:
            pass
        
        return True
    
    def _check_location_similarity(self, report: OceanReport, incident: OceanIncident) -> bool:
        """
        Check if report and incident locations are similar.
        """
        
        # If both have coordinates, check distance
        if (report.latitude and report.longitude and 
            incident.latitude and incident.longitude):
            
            distance = self._haversine_distance(
                report.latitude, report.longitude,
                incident.latitude, incident.longitude
            )
            
            # Within 5 km
            return distance < self.location_threshold_km
        
        # If text locations, check if they match
        if report.location and incident.location:
            # Simple substring match
            return (report.location.lower() in incident.location.lower() or
                    incident.location.lower() in report.location.lower())
        
        # Default: allow merge if other criteria pass
        return True
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Compute TF-IDF cosine similarity between two texts."""
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2]).toarray()
            similarity = cosine_similarity([tfidf_matrix[0]], [tfidf_matrix[1]])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two coordinates."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km


def cluster_reports(reports: List[OceanReport]) -> List[OceanIncident]:
    """Quick function to cluster reports into incidents."""
    clusterer = IncidentClusterer()
    return clusterer.cluster_reports(reports)


def cluster_with_existing(new_reports: List[OceanReport]) -> Tuple[List[OceanIncident], Dict]:
    """Quick function to cluster new reports with existing incidents."""
    clusterer = IncidentClusterer()
    return clusterer.cluster_with_existing(new_reports)


# Import datetime for type hints
from datetime import datetime
