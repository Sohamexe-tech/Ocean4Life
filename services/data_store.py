"""
OceanShield AI - Data Storage Layer

Handles persistence of reports and incidents using JSON files.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from models.ocean_models import OceanReport, OceanIncident


class DataStore:
    """Simple JSON-based data store for reports and incidents."""
    
    def __init__(self, data_dir: str = "data/ocean_data"):
        self.data_dir = data_dir
        self.reports_file = os.path.join(data_dir, "reports.json")
        self.incidents_file = os.path.join(data_dir, "incidents.json")
        
        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Ensure files exist
        if not os.path.exists(self.reports_file):
            self._write_json(self.reports_file, {"reports": []})
        if not os.path.exists(self.incidents_file):
            self._write_json(self.incidents_file, {"incidents": []})
    
    # ── REPORTS ──────────────────────────────
    
    def save_report(self, report: OceanReport) -> bool:
        """Save a report to storage."""
        try:
            data = self._read_json(self.reports_file)
            report_dict = json.loads(report.model_dump_json())
            
            # Check if report already exists
            existing = next((r for r in data["reports"] if r["report_id"] == report.report_id), None)
            if existing:
                # Update existing
                idx = data["reports"].index(existing)
                data["reports"][idx] = report_dict
            else:
                # Add new
                data["reports"].append(report_dict)
            
            self._write_json(self.reports_file, data)
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def get_report(self, report_id: str) -> Optional[OceanReport]:
        """Get a report by ID."""
        try:
            data = self._read_json(self.reports_file)
            for r in data["reports"]:
                if r["report_id"] == report_id:
                    return OceanReport(**r)
        except Exception as e:
            print(f"Error getting report: {e}")
        return None
    
    def get_all_reports(self) -> List[OceanReport]:
        """Get all reports."""
        try:
            data = self._read_json(self.reports_file)
            return [OceanReport(**r) for r in data.get("reports", [])]
        except Exception as e:
            print(f"Error getting reports: {e}")
        return []
    
    def get_reports_by_status(self, status: str) -> List[OceanReport]:
        """Get reports by status."""
        try:
            all_reports = self.get_all_reports()
            return [r for r in all_reports if r.status == status]
        except Exception as e:
            print(f"Error filtering reports: {e}")
        return []
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report."""
        try:
            data = self._read_json(self.reports_file)
            data["reports"] = [r for r in data["reports"] if r["report_id"] != report_id]
            self._write_json(self.reports_file, data)
            return True
        except Exception as e:
            print(f"Error deleting report: {e}")
            return False
    
    # ── INCIDENTS ────────────────────────────
    
    def save_incident(self, incident: OceanIncident) -> bool:
        """Save an incident to storage."""
        try:
            data = self._read_json(self.incidents_file)
            incident_dict = json.loads(incident.model_dump_json())
            
            # Check if incident already exists
            existing = next((i for i in data["incidents"] if i["incident_id"] == incident.incident_id), None)
            if existing:
                # Update existing
                idx = data["incidents"].index(existing)
                data["incidents"][idx] = incident_dict
            else:
                # Add new
                data["incidents"].append(incident_dict)
            
            self._write_json(self.incidents_file, data)
            return True
        except Exception as e:
            print(f"Error saving incident: {e}")
            return False
    
    def get_incident(self, incident_id: str) -> Optional[OceanIncident]:
        """Get an incident by ID."""
        try:
            data = self._read_json(self.incidents_file)
            for i in data["incidents"]:
                if i["incident_id"] == incident_id:
                    return OceanIncident(**i)
        except Exception as e:
            print(f"Error getting incident: {e}")
        return None
    
    def get_all_incidents(self) -> List[OceanIncident]:
        """Get all incidents."""
        try:
            data = self._read_json(self.incidents_file)
            return [OceanIncident(**i) for i in data.get("incidents", [])]
        except Exception as e:
            print(f"Error getting incidents: {e}")
        return []
    
    def get_incidents_by_status(self, status: str) -> List[OceanIncident]:
        """Get incidents by status."""
        try:
            all_incidents = self.get_all_incidents()
            return [i for i in all_incidents if i.status == status]
        except Exception as e:
            print(f"Error filtering incidents: {e}")
        return []
    
    def get_incidents_by_hazard(self, hazard_type: str) -> List[OceanIncident]:
        """Get incidents by hazard type."""
        try:
            all_incidents = self.get_all_incidents()
            return [i for i in all_incidents if i.hazard_type == hazard_type]
        except Exception as e:
            print(f"Error filtering incidents: {e}")
        return []
    
    def get_incidents_by_severity(self, severity: str) -> List[OceanIncident]:
        """Get incidents by severity."""
        try:
            all_incidents = self.get_all_incidents()
            return [i for i in all_incidents if i.severity == severity]
        except Exception as e:
            print(f"Error filtering incidents: {e}")
        return []
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        try:
            reports = self.get_all_reports()
            incidents = self.get_all_incidents()
            
            return {
                "total_reports": len(reports),
                "pending_reports": len([r for r in reports if r.status == "PENDING"]),
                "classified_reports": len([r for r in reports if r.status == "CLASSIFIED"]),
                "total_incidents": len(incidents),
                "pending_incidents": len([i for i in incidents if i.status == "PENDING"]),
                "verified_incidents": len([i for i in incidents if i.status == "VERIFIED"]),
                "high_critical_incidents": len([i for i in incidents if i.severity in ["HIGH", "CRITICAL"]]),
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident."""
        try:
            data = self._read_json(self.incidents_file)
            data["incidents"] = [i for i in data["incidents"] if i["incident_id"] != incident_id]
            self._write_json(self.incidents_file, data)
            return True
        except Exception as e:
            print(f"Error deleting incident: {e}")
            return False
    
    # ── UTILITIES ────────────────────────────
    
    def _read_json(self, filepath: str) -> dict:
        """Read JSON file."""
        if not os.path.exists(filepath):
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_json(self, filepath: str, data: dict):
        """Write JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Global data store instance
_data_store = None

def get_data_store() -> DataStore:
    """Get global data store instance."""
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
    return _data_store
