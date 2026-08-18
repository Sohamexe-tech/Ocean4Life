/**
 * OceanShield Map Integration
 * Handles Leaflet map with GeoJSON incident markers
 */

const OceanShieldMap = {
    map: null,
    geojsonLayer: null,
    markersLayer: null,

    /**
     * Initialize the map
     */
    init(containerId = 'map') {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Create map centered on India
        this.map = L.map(containerId).setView([20, 78], 5);

        // Add dark tile layer (matching theme)
        const isDarkTheme = document.documentElement.dataset.theme !== 'light';
        const tileLayer = isDarkTheme
            ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
            : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

        L.tileLayer(tileLayer, {
            attribution: '© OpenStreetMap © CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        // Initialize layers
        this.markersLayer = L.featureGroup().addTo(this.map);

        // Load incidents
        this.loadIncidents();

        // Listen for theme changes
        document.addEventListener('themeChange', () => this.updateMapTiles());
    },

    /**
     * Load incidents from API and display on map
     */
    async loadIncidents() {
        try {
            const geojson = await OceanShieldAPI.getIncidentsGeoJSON();
            this.displayIncidents(geojson);
        } catch (error) {
            console.error('Error loading incidents for map:', error);
        }
    },

    /**
     * Display incidents on map from GeoJSON
     */
    displayIncidents(geojson) {
        // Clear existing markers
        this.markersLayer.clearLayers();

        if (!geojson.features || geojson.features.length === 0) {
            return;
        }

        // Add markers for each incident
        geojson.features.forEach(feature => {
            const coords = feature.geometry.coordinates;
            const props = feature.properties;

            const marker = L.circleMarker([coords[1], coords[0]], {
                radius: 6,
                fillColor: this.getSeverityColor(props.severity),
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            });

            const popupContent = `
        <div style="min-width: 200px; font-size: 12px;">
          <div style="font-weight: bold; margin-bottom: 8px; color: #ff2d2d;">${props.incident_id}</div>
          <div style="margin-bottom: 4px;"><strong>Hazard:</strong> ${props.hazard_type}</div>
          <div style="margin-bottom: 4px;"><strong>Severity:</strong> <span style="font-weight: bold; color: ${this.getSeverityColor(props.severity)}">${props.severity}</span></div>
          <div style="margin-bottom: 4px;"><strong>Credibility:</strong> ${props.credibility_score}/100</div>
          <div style="margin-bottom: 4px;"><strong>Location:</strong> ${props.location}</div>
          <div style="margin-bottom: 4px;"><strong>Reports:</strong> ${props.report_count}</div>
          <div style="margin-bottom: 8px;"><strong>Status:</strong> <span style="font-weight: bold;">${props.status}</span></div>
          <button onclick="OceanShieldUI.showIncidentDetail('${props.incident_id}')" style="background: #ff2d2d; color: white; border: none; border-radius: 4px; padding: 6px 12px; cursor: pointer; font-weight: bold; width: 100%;">View Details</button>
        </div>
      `;

            marker.bindPopup(popupContent);
            marker.addTo(this.markersLayer);
        });

        // Fit map to all markers
        if (this.markersLayer.getLayers().length > 0) {
            this.map.fitBounds(this.markersLayer.getBounds(), { padding: [50, 50] });
        }
    },

    /**
     * Get color for severity level
     */
    getSeverityColor(severity) {
        const colors = {
            'CRITICAL': '#ff2d2d',  // red
            'HIGH': '#ff7a00',      // orange
            'MODERATE': '#ffd600',  // yellow
            'LOW': '#00e676'        // green
        };
        return colors[severity] || '#6b7280';  // muted gray
    },

    /**
     * Update map tiles when theme changes
     */
    updateMapTiles() {
        if (!this.map) return;

        const isDarkTheme = document.documentElement.dataset.theme !== 'light';
        const tileUrl = isDarkTheme
            ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
            : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

        // Remove old tile layer
        this.map.eachLayer(layer => {
            if (layer instanceof L.TileLayer) {
                this.map.removeLayer(layer);
            }
        });

        // Add new tile layer
        L.tileLayer(tileUrl, {
            attribution: '© OpenStreetMap © CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);
    },

    /**
     * Refresh map with latest incidents
     */
    async refresh() {
        await this.loadIncidents();
    }
};

// Initialize map when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('map')) {
        OceanShieldMap.init('map');
    }
});
