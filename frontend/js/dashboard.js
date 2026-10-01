// Dashboard Metrics and Visualizations Controller

const Dashboard = {
  charts: {},

  init() {
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById("btn-load-demo-topbar")?.addEventListener("click", () => this.loadDemoData());
  },

  async loadSummary() {
    try {
      const summary = await API.get("/api/conflicts/summary");
      this.updateStatsCards(summary);
      this.renderCharts(summary);
      this.loadRecentConflicts();
    } catch (err) {
      console.error("Failed to load dashboard summary:", err);
    }
  },

  updateStatsCards(summary) {
    document.getElementById("stat-documents").textContent = summary.total_documents || 0;
    document.getElementById("stat-requirements").textContent = summary.total_requirements || 0;
    document.getElementById("stat-relationships").textContent = summary.total_relationships || 0;
    document.getElementById("stat-critical").textContent = summary.critical_conflicts || 0;
    document.getElementById("stat-overlaps").textContent = (summary.semantic_overlaps || 0) + (summary.duplicates || 0);
  },

  renderCharts(summary) {
    // 1. Severity Distribution Donut Chart
    const ctxSev = document.getElementById("chart-severity")?.getContext("2d");
    if (ctxSev) {
      if (this.charts.severity) this.charts.severity.destroy();
      
      const sevData = [
        summary.critical_conflicts || 0,
        summary.high_conflicts || 0,
        summary.medium_conflicts || 0,
        summary.low_conflicts || 0
      ];

      this.charts.severity = new Chart(ctxSev, {
        type: 'doughnut',
        data: {
          labels: ['Critical', 'High', 'Medium', 'Low'],
          datasets: [{
            data: sevData,
            backgroundColor: ['#ef4444', '#f97316', '#eab308', '#3b82f6'],
            borderColor: '#111622',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: '#94a3b8', font: { size: 11, family: 'Inter' } }
            }
          },
          cutout: '70%'
        }
      });
    }

    // 2. Conflict Type Horizontal Bar Chart
    const ctxType = document.getElementById("chart-type")?.getContext("2d");
    if (ctxType) {
      if (this.charts.type) this.charts.type.destroy();

      const typeLabels = ['Contradiction', 'Partial', 'Overlap', 'Duplicate', 'Ambiguity'];
      const typeData = [
        summary.direct_contradictions || 0,
        summary.partial_conflicts || 0,
        summary.semantic_overlaps || 0,
        summary.duplicates || 0,
        summary.ambiguities || 0
      ];

      this.charts.type = new Chart(ctxType, {
        type: 'bar',
        data: {
          labels: typeLabels,
          datasets: [{
            label: 'Detected',
            data: typeData,
            backgroundColor: ['#ef4444', '#f97316', '#06b6d4', '#a855f7', '#eab308'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: '#94a3b8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } }
          }
        }
      });
    }

    // 3. Conflicts by Document Bar Chart
    const ctxDoc = document.getElementById("chart-document")?.getContext("2d");
    if (ctxDoc) {
      if (this.charts.document) this.charts.document.destroy();

      const docLabels = Object.keys(summary.conflicts_by_document || {});
      const docData = Object.values(summary.conflicts_by_document || {});

      this.charts.document = new Chart(ctxDoc, {
        type: 'bar',
        data: {
          labels: docLabels.length ? docLabels.map(l => l.length > 18 ? l.substring(0, 16) + '...' : l) : ['No Docs'],
          datasets: [{
            label: 'Conflicts',
            data: docData.length ? docData : [0],
            backgroundColor: '#6366f1',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: '#94a3b8', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } }
          }
        }
      });
    }
  },

  async loadRecentConflicts() {
    const tbody = document.getElementById("dashboard-recent-conflicts-tbody");
    if (!tbody) return;

    try {
      const conflicts = await API.get("/api/conflicts?limit=5");
      if (!conflicts || conflicts.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; color: var(--text-dim); padding: 36px;">
              No conflicts analyzed yet. Click <strong>Load Demo Workspace</strong> or upload documents to get started.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = conflicts.slice(0, 5).map(c => `
        <tr>
          <td><span class="ref-tag" onclick="window.Comparison?.openModal('${c.conflict_id}')">${c.conflict_id.substring(0, 8)}</span></td>
          <td>
            <span class="ref-tag" onclick="window.App?.jumpToRequirement('${c.requirement_1.requirement_id}')">${c.requirement_1.reference_code}</span>
            <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;">${c.requirement_1.source_document}</div>
          </td>
          <td>
            <span class="ref-tag" onclick="window.App?.jumpToRequirement('${c.requirement_2.requirement_id}')">${c.requirement_2.reference_code}</span>
            <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;">${c.requirement_2.source_document}</div>
          </td>
          <td><span class="badge badge-${c.conflict_type.toLowerCase().includes('contra') ? 'contradiction' : (c.conflict_type.toLowerCase().includes('over') ? 'overlap' : 'partial')}">${c.conflict_type}</span></td>
          <td><span class="badge badge-${c.severity.toLowerCase()}">${c.severity}</span></td>
          <td style="max-width: 280px; font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;">${c.explanation}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="window.Comparison?.openModal('${c.conflict_id}')">
              <i data-lucide="split" style="width: 13px; height: 13px;"></i>
              <span>Inspect</span>
            </button>
          </td>
        </tr>
      `).join("");

      lucide.createIcons();
    } catch (err) {
      console.error("Failed to load recent conflicts:", err);
    }
  },

  async loadDemoData() {
    try {
      window.showToast("Loading fictional SRS and BRD requirement documents...", "info");
      const res = await API.post("/api/demo/load");
      window.showToast("Demo workspace loaded & semantic conflict analysis complete!", "success");
      
      // Refresh all views
      await this.loadSummary();
      await window.Documents?.loadDocuments();
      await window.Requirements?.loadRequirements();
      await window.Conflicts?.loadConflicts();
      await window.Reports?.loadReport();
    } catch (err) {
      console.error("Failed to load demo data:", err);
      window.showToast(`Failed to load demo data: ${err.message}`, "error");
    }
  }
};

window.Dashboard = Dashboard;
