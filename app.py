import re
import json
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from real_news_disaster_search import RealNewsDisasterSearch

# OceanShield Phase 2 imports
from services.report_processor import process_citizen_report
from services.incident_clusterer import cluster_with_existing
from services.data_store import get_data_store

app        = Flask(__name__)
searcher   = RealNewsDisasterSearch()
geolocator = Nominatim(user_agent="disaster_relief_scout")
data_store = get_data_store()

URL_PATTERN = re.compile(r'https?://\S+')


@app.route('/', methods=['GET', 'POST'])
def home():
    city_or_url     = None
    incidents       = []
    real_news       = []
    ai_reports      = []
    lat = lon       = None
    error           = None
    news_analysis   = None
    incident_coords = []

    if request.method == 'POST':
        city_or_url = request.form.get('city_or_url', '').strip()

        if not city_or_url:
            error = "Please enter a city name or news URL."

        elif URL_PATTERN.match(city_or_url):
            try:
                news_analysis = searcher.analyze_news_url(city_or_url)
            except Exception as e:
                error = f"Fact-check error: {e}"

        else:
            try:
                data = searcher.search_city(city_or_url, return_data=True)

                if data is None:
                    data = {}

                real_news  = data.get("real_news",  [])
                ai_reports = data.get("ai_reports", [])
                incidents  = data.get("incidents",  [])

                try:
                    location = geolocator.geocode(city_or_url, timeout=10)
                    if location:
                        lat, lon = location.latitude, location.longitude
                except Exception:
                    pass

                for inc in incidents:
                    if not inc.location:
                        continue
                    try:
                        loc = geolocator.geocode(inc.location, timeout=5)
                        if loc:
                            incident_coords.append({
                                "lat":     loc.latitude,
                                "lon":     loc.longitude,
                                "type":    inc.need_type,
                                "summary": inc.summary,
                                "urgency": inc.urgency
                            })
                    except Exception:
                        pass

            except Exception as e:
                error = f"Error occurred: {e}"

    return render_template(
        'index.html',
        city_or_url     = city_or_url,
        incidents       = incidents,
        real_news       = real_news,
        ai_reports      = ai_reports,
        lat             = lat,
        lon             = lon,
        error           = error,
        news_analysis   = news_analysis,
        incident_coords = incident_coords
    )


# ════════════════════════════════════════════════════════════════════════
# OCEANSHIELD PHASE 2 - CITIZEN REPORTING API
# ════════════════════════════════════════════════════════════════════════

@app.route('/api/reports', methods=['POST'])
def submit_citizen_report():
    """
    POST: Submit a new citizen hazard report
    
    Payload:
    {
        "description": "Water flooding coastal roads",
        "location": "Mumbai, India",
        "latitude": 19.0760,    (optional)
        "longitude": 72.8777,   (optional)
        "reporter_name": "John Doe",  (optional)
        "is_demo": false
    }
    
    Returns:
        {
            "success": true,
            "report_id": "OS-RPT-ABC123",
            "status": "CLASSIFIED",
            "hazard_type": "COASTAL_FLOODING",
            "severity": "HIGH",
            "credibility_score": 75,
            "metadata": {...}
        }
    """
    try:
        payload = request.get_json() or {}
        
        # Validate required fields
        if not payload.get('description'):
            return jsonify({"error": "Description required"}), 400
        if not payload.get('location'):
            return jsonify({"error": "Location required"}), 400
        
        # Process report
        report, metadata = process_citizen_report(
            description=payload.get('description', ''),
            location=payload.get('location', ''),
            latitude=payload.get('latitude'),
            longitude=payload.get('longitude'),
            reporter_name=payload.get('reporter_name'),
            is_demo=payload.get('is_demo', False)
        )
        
        # Save to storage
        data_store.save_report(report)
        
        # Try to cluster with existing incidents
        incidents, cluster_metadata = cluster_with_existing([report])
        
        # Save any new/updated incidents
        for incident in incidents:
            data_store.save_incident(incident)
        
        return jsonify({
            "success": True,
            "report_id": report.report_id,
            "status": report.status,
            "hazard_type": report.hazard_type,
            "severity": metadata.get("severity_evidence", ["PENDING"])[0] if metadata.get("severity_evidence") else "PENDING",
            "credibility_score": metadata.get("credibility_score", 50),
            "location": report.location,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "metadata": {
                "processing_steps": metadata.get("steps", []),
                "credibility_factors": metadata.get("credibility_factors", {}),
                "clustering": cluster_metadata
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports', methods=['GET'])
def get_all_reports():
    """GET: Get all citizen reports with optional filtering"""
    try:
        status = request.args.get('status')  # e.g., ?status=CLASSIFIED
        
        if status:
            reports = data_store.get_reports_by_status(status)
        else:
            reports = data_store.get_all_reports()
        
        # Convert to JSON-serializable format
        report_list = []
        for r in reports:
            report_dict = json.loads(r.model_dump_json())
            report_list.append(report_dict)
        
        return jsonify({
            "success": True,
            "count": len(report_list),
            "reports": report_list
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """GET: Get a specific report by ID"""
    try:
        report = data_store.get_report(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404
        
        report_dict = json.loads(report.model_dump_json())
        return jsonify({
            "success": True,
            "report": report_dict
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/incidents', methods=['GET'])
def get_all_incidents():
    """GET: Get all incidents with optional filtering"""
    try:
        status = request.args.get('status')        # e.g., ?status=VERIFIED
        hazard = request.args.get('hazard')        # e.g., ?hazard=COASTAL_FLOODING
        severity = request.args.get('severity')    # e.g., ?severity=HIGH
        
        all_incidents = data_store.get_all_incidents()
        
        # Filter
        if status:
            all_incidents = [i for i in all_incidents if i.status == status]
        if hazard:
            all_incidents = [i for i in all_incidents if i.hazard_type == hazard]
        if severity:
            all_incidents = [i for i in all_incidents if i.severity == severity]
        
        # Convert to JSON
        incident_list = []
        for inc in all_incidents:
            inc_dict = json.loads(inc.model_dump_json())
            incident_list.append(inc_dict)
        
        return jsonify({
            "success": True,
            "count": len(incident_list),
            "incidents": incident_list
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/incidents/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    """GET: Get a specific incident by ID"""
    try:
        incident = data_store.get_incident(incident_id)
        if not incident:
            return jsonify({"error": "Incident not found"}), 404
        
        inc_dict = json.loads(incident.model_dump_json())
        return jsonify({
            "success": True,
            "incident": inc_dict
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/incidents/<incident_id>', methods=['PUT'])
def update_incident_status(incident_id):
    """PUT: Update incident status"""
    try:
        incident = data_store.get_incident(incident_id)
        if not incident:
            return jsonify({"error": "Incident not found"}), 404
        
        payload = request.get_json() or {}
        new_status = payload.get('status')  # VERIFIED, REJECTED, RESOLVED, etc.
        
        if not new_status:
            return jsonify({"error": "Status required"}), 400
        
        incident.status = new_status
        data_store.save_incident(incident)
        
        inc_dict = json.loads(incident.model_dump_json())
        return jsonify({
            "success": True,
            "incident": inc_dict
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """GET: Get dashboard summary statistics"""
    try:
        stats = data_store.get_dashboard_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/map/incidents', methods=['GET'])
def get_incidents_geojson():
    """GET: Get incidents as GeoJSON for map visualization"""
    try:
        incidents = data_store.get_all_incidents()
        
        features = []
        for inc in incidents:
            if inc.latitude and inc.longitude:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [inc.longitude, inc.latitude]
                    },
                    "properties": {
                        "incident_id": inc.incident_id,
                        "hazard_type": inc.hazard_type,
                        "severity": inc.severity,
                        "credibility_score": inc.ai_credibility_score,
                        "location": inc.location,
                        "status": inc.status,
                        "report_count": inc.report_count
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return jsonify(geojson)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)