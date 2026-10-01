// Conflict Reports and Export Controller

const Reports = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById("btn-export-csv")?.addEventListener("click", () => this.downloadExport("csv"));
    document.getElementById("btn-export-json")?.addEventListener("click", () => this.downloadExport("json"));
    document.getElementById("btn-export-md")?.addEventListener("click", () => this.downloadExport("md"));
  },

  async loadReport() {
    const container = document.getElementById("report-rendered-content");
    if (!container) return;

    try {
      const summary = await API.get("/api/conflicts/summary");
      const conflicts = await API.get("/api/conflicts");

      container.innerHTML = `
        <div style="border-bottom: 2px solid var(--border-subtle); padding-bottom: 20px; margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <h2 style="font-size: 1.5rem; color: #fff; font-weight: 800;">Software Requirements Conflict & Overlap Audit Report</h2>
              <p style="color: var(--text-muted); font-size: 0.88rem; margin-top: 4px;">Formal Engineering Verification & Specification Consistency Assessment</p>
            </div>
            <div style="text-align: right; font-size: 0.82rem; color: var(--text-dim);">
              <div>Generated: ${new Date().toLocaleDateString()}</div>
              <div>System: ReqConflict AI Auditor</div>
            </div>
          </div>
        </div>

        <div style="margin-bottom: 28px;">
          <h3 style="font-size: 1.1rem; color: #fff; font-weight: 700; margin-bottom: 14px;">1. Executive Summary</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 18px;">
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 14px;">
              <div style="font-size: 0.76rem; color: var(--text-muted); text-transform: uppercase;">Documents Analyzed</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #fff; margin-top: 4px;">${summary.total_documents}</div>
            </div>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 14px;">
              <div style="font-size: 0.76rem; color: var(--text-muted); text-transform: uppercase;">Total Requirements</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #fff; margin-top: 4px;">${summary.total_requirements}</div>
            </div>
            <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid var(--sev-critical-border); border-radius: var(--radius-md); padding: 14px;">
              <div style="font-size: 0.76rem; color: #fca5a5; text-transform: uppercase;">Critical Contradictions</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #f87171; margin-top: 4px;">${summary.critical_conflicts}</div>
            </div>
            <div style="background: rgba(249, 115, 22, 0.08); border: 1px solid var(--sev-high-border); border-radius: var(--radius-md); padding: 14px;">
              <div style="font-size: 0.76rem; color: #fdba74; text-transform: uppercase;">High Severity Conflicts</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #fb923c; margin-top: 4px;">${summary.high_conflicts}</div>
            </div>
            <div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: var(--radius-md); padding: 14px;">
              <div style="font-size: 0.76rem; color: #67e8f9; text-transform: uppercase;">Semantic Overlaps</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #38bdf8; margin-top: 4px;">${summary.semantic_overlaps + summary.duplicates}</div>
            </div>
          </div>
        </div>

        <div>
          <h3 style="font-size: 1.1rem; color: #fff; font-weight: 700; margin-bottom: 14px;">2. Detailed Conflict & Inconsistency Findings (${conflicts.length})</h3>
          
          ${conflicts.length === 0 ? `
            <p style="color: var(--text-dim); padding: 24px 0;">No conflicts detected.</p>
          ` : `
            <div style="display: flex; flex-direction: column; gap: 20px;">
              ${conflicts.map((c, i) => `
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 20px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                      <span style="font-weight: 800; color: #fff; font-size: 0.95rem;">#${i + 1}</span>
                      <span class="ref-tag">${c.conflict_id.substring(0, 10)}</span>
                      <span class="badge badge-${c.conflict_type.toLowerCase().includes('contra') ? 'contradiction' : 'partial'}">${c.conflict_type}</span>
                    </div>
                    <span class="badge badge-${c.severity.toLowerCase()}">${c.severity} Severity</span>
                  </div>

                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div style="background: rgba(0,0,0,0.25); border-radius: var(--radius-md); padding: 12px; border-left: 3px solid #6366f1;">
                      <div style="font-size: 0.74rem; color: var(--text-muted); margin-bottom: 4px;">
                        <strong>${c.requirement_1.reference_code}</strong> | ${c.requirement_1.source_document} (${c.requirement_1.section}${c.requirement_1.page_number ? `, Page ${c.requirement_1.page_number}` : ''})
                      </div>
                      <div style="font-size: 0.86rem; color: #f8fafc; font-style: italic;">"${c.requirement_1.requirement_text}"</div>
                    </div>
                    <div style="background: rgba(0,0,0,0.25); border-radius: var(--radius-md); padding: 12px; border-left: 3px solid #06b6d4;">
                      <div style="font-size: 0.74rem; color: var(--text-muted); margin-bottom: 4px;">
                        <strong>${c.requirement_2.reference_code}</strong> | ${c.requirement_2.source_document} (${c.requirement_2.section}${c.requirement_2.page_number ? `, Page ${c.requirement_2.page_number}` : ''})
                      </div>
                      <div style="font-size: 0.86rem; color: #f8fafc; font-style: italic;">"${c.requirement_2.requirement_text}"</div>
                    </div>
                  </div>

                  <div style="font-size: 0.86rem; color: var(--text-main); margin-bottom: 10px;">
                    <strong>Semantic Conflict Explanation:</strong> ${c.explanation}
                  </div>

                  ${c.conflicting_elements ? `
                    <div style="font-size: 0.82rem; color: #fca5a5; background: var(--sev-critical-bg); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;">
                      <strong>Conflicting Conditions:</strong> ${c.conflicting_elements}
                    </div>
                  ` : ''}

                  ${c.suggested_clarification ? `
                    <div style="font-size: 0.82rem; color: #67e8f9; background: rgba(6, 182, 212, 0.08); padding: 8px 12px; border-radius: 6px;">
                      <strong>Suggested Clarification:</strong> ${c.suggested_clarification}
                    </div>
                  ` : ''}
                </div>
              `).join("")}
            </div>
          `}
        </div>
      `;

      lucide.createIcons();
    } catch (err) {
      console.error("Failed to load report view:", err);
    }
  },

  async downloadExport(format) {
    try {
      window.showToast(`Preparing ${format.toUpperCase()} export...`, "info");
      const token = API.getToken();
      const res = await fetch(`/api/conflicts/export/${format}`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });

      if (!res.ok) throw new Error("Export download failed");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `requirement_conflicts_report.${format === 'md' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      window.showToast(`${format.toUpperCase()} report downloaded successfully.`, "success");
    } catch (err) {
      window.showToast(`Export error: ${err.message}`, "error");
    }
  }
};

window.Reports = Reports;
