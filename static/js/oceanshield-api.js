/**
 * OceanShield API Wrapper
 * Handles all communication with backend REST APIs
 */

const OceanShieldAPI = {
    baseURL: '',

    /**
     * Submit a new citizen hazard report
     */
    async submitReport(data) {
        try {
            const response = await fetch('/api/reports', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Report submission error:', error);
            throw error;
        }
    },

    /**
     * Get all citizen reports
     */
    async getAllReports(status = null) {
        try {
            let url = '/api/reports';
            if (status) url += `?status=${encodeURIComponent(status)}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.reports || [];
        } catch (error) {
            console.error('Error fetching reports:', error);
            return [];
        }
    },

    /**
     * Get a specific report by ID
     */
    async getReport(reportId) {
        try {
            const response = await fetch(`/api/reports/${reportId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.report || null;
        } catch (error) {
            console.error('Error fetching report:', error);
            return null;
        }
    },

    /**
     * Get all incidents
     */
    async getAllIncidents(filters = {}) {
        try {
            let url = '/api/incidents';
            const params = new URLSearchParams();

            if (filters.status) params.append('status', filters.status);
            if (filters.hazard) params.append('hazard', filters.hazard);
            if (filters.severity) params.append('severity', filters.severity);

            if (params.toString()) url += `?${params.toString()}`;

            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.incidents || [];
        } catch (error) {
            console.error('Error fetching incidents:', error);
            return [];
        }
    },

    /**
     * Get a specific incident by ID
     */
    async getIncident(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.incident || null;
        } catch (error) {
            console.error('Error fetching incident:', error);
            return null;
        }
    },

    /**
     * Update incident status
     */
    async updateIncidentStatus(incidentId, status) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.incident || null;
        } catch (error) {
            console.error('Error updating incident:', error);
            throw error;
        }
    },

    /**
     * Get dashboard statistics
     */
    async getDashboardStats() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            return data.stats || {};
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
            return {};
        }
    },

    /**
     * Get incidents as GeoJSON for map
     */
    async getIncidentsGeoJSON() {
        try {
            const response = await fetch('/api/map/incidents');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            return await response.json();
        } catch (error) {
            console.error('Error fetching GeoJSON:', error);
            return { type: 'FeatureCollection', features: [] };
        }
    }
};
