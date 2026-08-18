/**
 * OceanShield UI Management
 * Handles dashboard, incidents, reports, and modals
 */

const OceanShieldUI = {
    state: {
        currentTab: 'dashboard',
        selectedIncident: null,
        dashboardStats: {},
        incidents: [],
        reports: [],
        filters: {
            hazard: 'all',
            severity: 'all',
            status: 'all'
        }
    },

    // ── INITIALIZATION ──

    async init() {
        this.setupEventListeners();
        await this.refreshDashboard();
    },

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('[data-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Report form
        const reportForm = document.getElementById('citizen-report-form');
        if (reportForm) {
            reportForm.addEventListener('submit', (e) => this.handleReportSubmit(e));
        }

        // Geolocation button
        const geoBtn = document.getElementById('geo-location-btn');
        if (geoBtn) {
            geoBtn.addEventListener('click', () => this.getGeolocation());
        }

        // Dashboard refresh
        const refreshBtn = document.getElementById('refresh-dashboard-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshDashboard());
        }

        // Filters
        document.querySelectorAll('[data-filter]').forEach(select => {
            select.addEventListener('change', (e) => {
                const filterName = e.target.dataset.filter;
                this.state.filters[filterName] = e.target.value;
                this.applyFilters();
            });
        });

        // Incident detail close
        const closeBtn = document.getElementById('incident-detail-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeIncidentDetail());
        }
    },

    // ── TAB MANAGEMENT ──

    switchTab(tab) {
        this.state.currentTab = tab;

        // Update button active states
        document.querySelectorAll('[data-tab]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // Update section visibility
        document.querySelectorAll('[data-section]').forEach(section => {
            section.style.display = section.dataset.section === tab ? 'block' : 'none';
        });

        // Load data for the selected tab
        if (tab === 'dashboard') this.refreshDashboard();
        else if (tab === 'incidents') this.refreshIncidents();
        else if (tab === 'reports') this.refreshReports();
    },

    // ── DASHBOARD ──

    async refreshDashboard() {
        try {
            const stats = await OceanShieldAPI.getDashboardStats();
            this.state.dashboardStats = stats;
            this.renderDashboard(stats);
        } catch (error) {
            this.showError('Failed to load dashboard statistics');
        }
    },

    renderDashboard(stats) {
        const cards = {
            totalReports: document.getElementById('stat-total-reports'),
            activeIncidents: document.getElementById('stat-active-incidents'),
            verifiedIncidents: document.getElementById('stat-verified-incidents'),
            highCritical: document.getElementById('stat-high-critical-incidents'),
            pendingReports: document.getElementById('stat-pending-reports')
        };

        if (cards.totalReports) cards.totalReports.textContent = stats.total_reports || 0;
        if (cards.activeIncidents) cards.activeIncidents.textContent = stats.total_incidents || 0;
        if (cards.verifiedIncidents) cards.verifiedIncidents.textContent = stats.verified_incidents || 0;
        if (cards.highCritical) cards.highCritical.textContent = stats.high_critical_incidents || 0;
        if (cards.pendingReports) cards.pendingReports.textContent = stats.pending_reports || 0;
    },

    // ── CITIZEN REPORT FORM ──

    async handleReportSubmit(e) {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const data = {
            description: formData.get('description'),
            location: formData.get('location'),
            latitude: formData.get('latitude'),
            longitude: formData.get('longitude'),
            reporter_name: formData.get('reporter_name'),
            is_demo: formData.get('is_demo') === 'on'
        };

        // Validate
        const validation = OceanShieldValidation.validateReport(data);
        if (!validation.valid) {
            this.showError(OceanShieldValidation.formatErrors(validation.errors));
            return;
        }

        // Clean data
        const cleanData = OceanShieldValidation.normalizeReport(data);

        // Submit
        try {
            this.showLoading('Submitting report...');
            const result = await OceanShieldAPI.submitReport(cleanData);

            // Show success modal with report details
            this.showReportSuccess(result);

            // Reset form
            form.reset();

            // Refresh dashboard and incidents
            setTimeout(() => {
                this.refreshDashboard();
                this.refreshIncidents();
            }, 1500);
        } catch (error) {
            this.showError(`Failed to submit report: ${error.message}`);
        }
    },

    showReportSuccess(result) {
        const modal = document.getElementById('report-success-modal');
        if (!modal) return;

        const content = `
      <div style="text-align: center; padding: 20px;">
        <div style="font-size: 32px; margin-bottom: 16px;">✅</div>
        <h3 style="margin-bottom: 20px; font-size: 18px;">Report Submitted Successfully</h3>
        
        <div style="background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: left; margin-bottom: 20px; font-size: 13px;">
          <div style="margin-bottom: 12px;">
            <strong>Report ID:</strong><br>
            <code style="color: var(--red);">${result.report_id}</code>
          </div>
          <div style="margin-bottom: 12px;">
            <strong>Detected Hazard:</strong><br>
            ${result.hazard_type || 'Analyzing...'}
          </div>
          <div style="margin-bottom: 12px;">
            <strong>AI-estimated Credibility:</strong><br>
            <strong>${result.credibility_score || 'N/A'}/100</strong>
          </div>
          <div style="margin-bottom: 12px;">
            <strong>Status:</strong><br>
            ${result.status}
          </div>
          <div style="margin-bottom: 0;">
            <strong>Location:</strong><br>
            ${result.location || 'Unknown'}
          </div>
        </div>

        <div style="font-size: 12px; color: var(--muted); line-height: 1.6; margin-bottom: 20px;">
          <p style="margin-bottom: 8px;">
            <strong>About credibility score:</strong>
          </p>
          <p>The AI-estimated credibility score (0-100) is based on available evidence and corroboration. It does not guarantee that a report is true.
          </p>
        </div>

        <button id="close-success-modal" style="background: var(--red); color: white; border: none; border-radius: 8px; padding: 10px 20px; cursor: pointer; font-weight: bold;">Close</button>
      </div>
    `;

        modal.innerHTML = content;
        modal.style.display = 'flex';

        document.getElementById('close-success-modal').addEventListener('click', () => {
            modal.style.display = 'none';
        });
    },

    getGeolocation() {
        if (!navigator.geolocation) {
            this.showError('Geolocation is not supported in your browser');
            return;
        }

        this.showLoading('Getting your location...');

        navigator.geolocation.getCurrentPosition(
            (position) => {
                document.getElementById('latitude').value = position.coords.latitude.toFixed(6);
                document.getElementById('longitude').value = position.coords.longitude.toFixed(6);
                this.hideLoading();
                this.showSuccess('Location captured successfully');
            },
            (error) => {
                this.hideLoading();
                this.showError(`Geolocation error: ${error.message}`);
            }
        );
    },

    // ── INCIDENTS ──

    async refreshIncidents() {
        try {
            this.showLoading('Loading incidents...');
            const incidents = await OceanShieldAPI.getAllIncidents(this.state.filters);
            this.state.incidents = incidents;
            this.renderIncidents(incidents);
            this.hideLoading();
        } catch (error) {
            this.showError('Failed to load incidents');
        }
    },

    renderIncidents(incidents) {
        const container = document.getElementById('incidents-table-body');
        if (!container) return;

        if (incidents.length === 0) {
            container.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: var(--muted);">No incidents found</td></tr>';
            return;
        }

        container.innerHTML = incidents.map(inc => `
      <tr style="cursor: pointer; transition: background 0.2s;" onclick="OceanShieldUI.showIncidentDetail('${inc.incident_id}')">
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--red);">${inc.incident_id}</td>
        <td>${inc.hazard_type}</td>
        <td>${inc.location || 'Unknown'}</td>
        <td>${this.renderSeverityBadge(inc.severity)}</td>
        <td>${this.renderCredibilityBadge(inc.ai_credibility_score)}</td>
        <td style="text-align: center;">${inc.report_count}</td>
        <td>${this.renderStatusBadge(inc.status)}</td>
        <td style="font-size: 11px; color: var(--muted);">${new Date(inc.created_at).toLocaleDateString()}</td>
      </tr>
    `).join('');
    },

    async showIncidentDetail(incidentId) {
        try {
            this.showLoading('Loading incident details...');
            const incident = await OceanShieldAPI.getIncident(incidentId);
            this.hideLoading();

            if (!incident) {
                this.showError('Incident not found');
                return;
            }

            this.state.selectedIncident = incident;
            this.renderIncidentDetail(incident);
        } catch (error) {
            this.showError('Failed to load incident details');
        }
    },

    renderIncidentDetail(incident) {
        const modal = document.getElementById('incident-detail-modal');
        if (!modal) return;

        const reportsHTML = (incident.reports || []).map(report => `
      <div style="background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 12px;">
        <div><strong>Report ID:</strong> <code style="color: var(--red);">${report.report_id}</code></div>
        <div><strong>Source:</strong> ${report.source}</div>
        <div style="margin-top: 8px; color: var(--muted);">${report.description.substring(0, 100)}...</div>
      </div>
    `).join('');

        const content = `
      <div style="padding: 20px; max-height: 80vh; overflow-y: auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h2 style="margin: 0;">${incident.incident_id}</h2>
          <button id="incident-detail-close" style="background: var(--surface2); border: 1px solid var(--border); color: var(--text); cursor: pointer; border-radius: 6px; padding: 8px 12px; font-size: 18px;">✕</button>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
          <div>
            <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Hazard Type</strong><br>
            ${incident.hazard_type}
          </div>
          <div>
            <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Severity</strong><br>
            ${this.renderSeverityBadge(incident.severity)}
          </div>
          <div>
            <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Credibility</strong><br>
            ${this.renderCredibilityBadge(incident.ai_credibility_score)}
          </div>
          <div>
            <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Status</strong><br>
            ${this.renderStatusBadge(incident.status)}
          </div>
        </div>

        <div style="background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 20px;">
          <strong>Location:</strong><br>
          <div style="margin-top: 4px; color: var(--text);">${incident.location || 'Unknown'}</div>
          ${incident.latitude ? `<div style="font-size: 11px; color: var(--muted); margin-top: 4px;">Coordinates: ${incident.latitude.toFixed(4)}, ${incident.longitude.toFixed(4)}</div>` : ''}
        </div>

        <div style="margin-bottom: 20px;">
          <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Evidence</strong><br>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
            ${(incident.evidence || []).map(e => `<span style="background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-size: 11px;">${e}</span>`).join('')}
          </div>
        </div>

        <div style="margin-bottom: 20px;">
          <strong style="color: var(--muted); font-size: 11px; text-transform: uppercase;">Linked Reports (${incident.report_count})</strong><br>
          <div style="margin-top: 8px;">
            ${reportsHTML}
          </div>
        </div>

        <div style="background: rgba(255, 212, 0, 0.1); border: 1px solid rgba(255, 212, 0, 0.3); border-radius: 8px; padding: 12px; font-size: 12px; color: var(--text);">
          <strong>About AI-estimated Credibility:</strong><br>
          <div style="margin-top: 6px; font-size: 11px; color: var(--muted);">The credibility score (0-100) is an AI/system estimate based on available evidence and corroboration. It does not guarantee that a report is true.</div>
        </div>
      </div>
    `;

        modal.innerHTML = content;
        modal.style.display = 'flex';

        document.getElementById('incident-detail-close').addEventListener('click', () => this.closeIncidentDetail());
    },

    closeIncidentDetail() {
        const modal = document.getElementById('incident-detail-modal');
        if (modal) modal.style.display = 'none';
    },

    // ── REPORTS ──

    async refreshReports() {
        try {
            this.showLoading('Loading reports...');
            const reports = await OceanShieldAPI.getAllReports();
            this.state.reports = reports;
            this.renderReports(reports);
            this.hideLoading();
        } catch (error) {
            this.showError('Failed to load reports');
        }
    },

    renderReports(reports) {
        const container = document.getElementById('reports-table-body');
        if (!container) return;

        if (reports.length === 0) {
            container.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--muted);">No reports found</td></tr>';
            return;
        }

        container.innerHTML = reports.map(report => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--red);">${report.report_id}</td>
        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${report.hazard_type || 'ANALYZING'}</td>
        <td>${report.location}</td>
        <td style="font-size: 12px;">${report.source}</td>
        <td>${this.renderStatusBadge(report.status)}</td>
        <td style="font-size: 11px; color: var(--muted);">${new Date(report.timestamp).toLocaleDateString()}</td>
        <td style="font-size: 11px; color: var(--muted);">${new Date(report.timestamp).toLocaleTimeString()}</td>
      </tr>
    `).join('');
    },

    // ── FILTERS ──

    applyFilters() {
        if (this.state.currentTab === 'incidents') {
            this.refreshIncidents();
        }
    },

    // ── RENDERING HELPERS ──

    renderSeverityBadge(severity) {
        const colors = {
            LOW: '--green',
            MODERATE: '--yellow',
            HIGH: '--orange',
            CRITICAL: '--red',
            PENDING: '--muted'
        };

        const color = colors[severity] || '--muted';
        return `<span style="background: rgba(var(--color-rgb), 0.15); color: var(${color}); border: 1px solid var(${color}); border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold; text-transform: uppercase;">${severity}</span>`;
    },

    renderCredibilityBadge(score) {
        let level = 'LOW';
        let color = '--red';

        if (score >= 80) { level = 'VERY HIGH'; color = '--green'; }
        else if (score >= 60) { level = 'HIGH'; color = '--blue'; }
        else if (score >= 40) { level = 'MODERATE'; color = '--yellow'; }

        return `<span style="background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold;" title="${score}/100">${score}/100</span>`;
    },

    renderStatusBadge(status) {
        const colors = {
            PENDING: '--yellow',
            ANALYZING: '--blue',
            CLASSIFIED: '--green',
            UNDER_REVIEW: '--orange',
            VERIFIED: '--green',
            REJECTED: '--red',
            RESOLVED: '--blue',
            FAILED: '--red'
        };

        const color = colors[status] || '--muted';
        return `<span style="background: var(--surface2); border: 1px solid var(--border); color: var(${color}); border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold; text-transform: uppercase;">${status}</span>`;
    },

    // ── NOTIFICATIONS ──

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('active');
            const text = overlay.querySelector('.loading-text');
            if (text) text.textContent = message;
        }
    },

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.remove('active');
    },

    showError(message) {
        const container = document.getElementById('error-container');
        if (!container) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-bar';
        errorDiv.innerHTML = `⚠️ ${message}`;
        container.appendChild(errorDiv);

        setTimeout(() => errorDiv.remove(), 5000);
    },

    showSuccess(message) {
        const container = document.getElementById('error-container');
        if (!container) return;

        const successDiv = document.createElement('div');
        successDiv.style.cssText = 'background: rgba(0,230,118,0.1); border: 1px solid rgba(0,230,118,0.3); color: var(--green); border-radius: 8px; padding: 12px 18px; font-size: 13px; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;';
        successDiv.innerHTML = `✅ ${message}`;
        container.appendChild(successDiv);

        setTimeout(() => successDiv.remove(), 3000);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    OceanShieldUI.init();
});
