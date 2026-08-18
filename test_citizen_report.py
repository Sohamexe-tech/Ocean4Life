#!/usr/bin/env python3
"""
Test script: Create citizen hazard reports and watch them flow through
the OceanShield Phase 2 pipeline.

Demonstrates:
1. Citizen report creation with location
2. AI classification (hazard type + confidence)
3. Severity assessment
4. Credibility scoring
5. Incident clustering
6. Dashboard statistics
"""

import json
from datetime import datetime
from services.report_processor import process_citizen_report
from services.incident_clusterer import cluster_with_existing
from services.data_store import get_data_store


def print_header(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_report_summary(report, metadata):
    """Pretty print a report and its processing metadata"""
    print(f"📋 Report ID: {report.report_id}")
    print(f"   Location: {report.location} ({report.latitude}, {report.longitude})")
    print(f"   Source: {report.source}")
    print(f"   Status: {report.status}")
    print(f"\n🎯 Hazard Classification:")
    print(f"   Type: {report.hazard_type}")
    print(f"   Confidence: {report.hazard_confidence:.0%}")
    print(f"\n📊 Credibility Score: {metadata['credibility_score']}/100")
    print(f"   Factors: {json.dumps(metadata['credibility_factors'], indent=6)}")
    print(f"\n📝 Processing Steps:")
    for step in metadata['steps']:
        print(f"   → {step}")


def create_report_1():
    """Create first citizen report: Coastal flooding in Mumbai"""
    print_header("REPORT 1: Coastal Flooding in Mumbai")
    
    description = """
    Water is flooding the coastal areas of Marine Drive in Mumbai. 
    The situation is worsening with high tides and storms. 
    Multiple residential buildings are affected. 
    Roads are completely submerged with water level rising.
    """
    
    report, metadata = process_citizen_report(
        description=description.strip(),
        location="Marine Drive, Mumbai, India",
        latitude=19.0760,
        longitude=72.8777,
        reporter_name="Rajesh Kumar",
        is_demo=False
    )
    
    print_report_summary(report, metadata)
    return report


def create_report_2():
    """Create second citizen report: Storm surge in Chennai"""
    print_header("REPORT 2: Storm Surge in Chennai")
    
    description = """
    Severe storm surge observed at Marina Beach Chennai. 
    Waves are crashing over the seawall. 
    Water is entering coastal businesses and shops. 
    Multiple boats damaged, fishing community affected.
    """
    
    report, metadata = process_citizen_report(
        description=description.strip(),
        location="Marina Beach, Chennai, India",
        latitude=13.0490,
        longitude=80.2828,
        reporter_name="Priya Sharma",
        is_demo=False
    )
    
    print_report_summary(report, metadata)
    return report


def create_report_3():
    """Create third citizen report: High waves in Goa"""
    print_header("REPORT 3: Dangerous High Waves in Goa")
    
    description = """
    Unusually high waves hitting Baga Beach in Goa. 
    Water level significantly higher than normal. 
    Swimmers warned to stay out of water. 
    Beach resorts evacuating guests to higher grounds.
    """
    
    report, metadata = process_citizen_report(
        description=description.strip(),
        location="Baga Beach, Goa, India",
        latitude=15.5859,
        longitude=73.7364,
        reporter_name="Amit Patel",
        is_demo=False
    )
    
    print_report_summary(report, metadata)
    return report


def create_report_4():
    """Create fourth citizen report: Oil spill detection"""
    print_header("REPORT 4: Marine Pollution - Oil Spill")
    
    description = """
    Dark oily slick observed floating near the coast.
    Strong petroleum smell in the air.
    Fish population showing signs of distress.
    Birds affected by the oil coating on water.
    """
    
    report, metadata = process_citizen_report(
        description=description.strip(),
        location="Thane, Maharashtra, India",
        latitude=19.2183,
        longitude=72.9781,
        reporter_name="Sarah Mendes",
        is_demo=False
    )
    
    print_report_summary(report, metadata)
    return report


def show_clustering_results(reports):
    """Show how reports cluster into incidents"""
    print_header("INCIDENT CLUSTERING RESULTS")
    
    incidents, metadata = cluster_with_existing(reports)
    
    print(f"📊 Clustering Summary:")
    print(f"   Input Reports: {len(reports)}")
    print(f"   New Incidents Created: {metadata['new_incidents']}")
    print(f"   Existing Incidents Updated: {metadata['updated_incidents']}")
    print(f"   Reports Merged: {metadata['merged_reports']}")
    
    print(f"\n📍 Incidents Generated:")
    for inc in incidents:
        print(f"\n   Incident ID: {inc.incident_id}")
        print(f"   Hazard Type: {inc.hazard_type}")
        print(f"   Location: {inc.location}")
        print(f"   Severity: {inc.severity}")
        print(f"   Credibility Score: {inc.ai_credibility_score}/100")
        print(f"   Credibility Level: {inc.credibility_level}")
        print(f"   Linked Reports: {inc.report_count}")
        print(f"   Status: {inc.status}")


def show_dashboard():
    """Show dashboard statistics"""
    print_header("OCEANSHIELD DASHBOARD STATISTICS")
    
    data_store = get_data_store()
    stats = data_store.get_dashboard_stats()
    
    print("📈 Summary Statistics:")
    print(f"   Total Citizen Reports: {stats.get('total_reports', 0)}")
    print(f"   Pending Reports: {stats.get('pending_reports', 0)}")
    print(f"   Classified Reports: {stats.get('classified_reports', 0)}")
    print(f"\n   Total Incidents: {stats.get('total_incidents', 0)}")
    print(f"   Pending Incidents: {stats.get('pending_incidents', 0)}")
    print(f"   Verified Incidents: {stats.get('verified_incidents', 0)}")
    print(f"   High/Critical Incidents: {stats.get('high_critical_incidents', 0)}")
    
    # Show all incidents
    all_incidents = data_store.get_all_incidents()
    if all_incidents:
        print(f"\n📋 All Incidents in System:")
        for inc in all_incidents:
            print(f"   • {inc.incident_id} | {inc.hazard_type:20s} | {inc.severity:8s} | Score: {inc.ai_credibility_score:3d}/100 | Reports: {inc.report_count}")


def main():
    """Run the complete test workflow"""
    
    print("\n" + "█"*70)
    print("█  OCEANSHIELD AI - Phase 2 Citizen Reporting Test")
    print("█"*70)
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create multiple reports
    report1 = create_report_1()
    report2 = create_report_2()
    report3 = create_report_3()
    report4 = create_report_4()
    
    # Save all reports
    data_store = get_data_store()
    for report in [report1, report2, report3, report4]:
        data_store.save_report(report)
        print(f"\n✓ Report {report.report_id} saved to storage")
    
    # Cluster reports into incidents
    all_reports = [report1, report2, report3, report4]
    show_clustering_results(all_reports)
    
    # Show dashboard
    show_dashboard()
    
    print_header("TEST COMPLETE")
    print("✅ All citizen reports processed successfully!")
    print("\n📡 API Endpoints Available:")
    print("   POST   /api/reports                    - Submit new citizen report")
    print("   GET    /api/reports                    - List all reports")
    print("   GET    /api/reports/<report_id>        - Get specific report")
    print("   GET    /api/incidents                  - List all incidents")
    print("   GET    /api/incidents/<incident_id>    - Get specific incident")
    print("   PUT    /api/incidents/<incident_id>    - Update incident status")
    print("   GET    /api/dashboard/stats            - Dashboard statistics")
    print("   GET    /api/map/incidents              - GeoJSON for map visualization")
    print("\n🌐 Start the web server:")
    print("   python app.py")
    print(f"\n✓ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
