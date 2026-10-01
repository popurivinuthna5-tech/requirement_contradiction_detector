// Conflict Analysis and Findings Explorer Controller

const Conflicts = {
  conflictsList: [],

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const searchInput = document.getElementById("conflict-search-input");
    const sevFilter = document.getElementById("conflict-filter-severity");
    const typeFilter = document.getElementById("conflict-filter-type");
    const docFilter = document.getElementById("conflict-filter-doc");
    const triggerBtn = document.getElementById("btn-trigger-analysis");

    let debounceTimer;
    searchInput?.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => this.loadConflicts(), 250);
    });

    sevFilter?.addEventListener("change", () => this.loadConflicts());
    typeFilter?.addEventListener("change", () => this.loadConflicts());
    docFilter?.addEventListener("change", () => this.loadConflicts());
    triggerBtn?.addEventListener("click", () => this.triggerAnalysis());
  },

  async triggerAnalysis() {
    try {
      window.showToast("Running semantic comparison & logical contradiction analysis...", "info");
      const res = await API.post("/api/conflicts/analyze", {
        similarity_threshold: 0.40
      });
      window.showToast(`Analysis completed! Found ${res.conflicts_found} findings.`, "success");
      
      await this.loadConflicts();
      await window.Dashboard?.loadSummary();
      await window.Reports?.loadReport();
    } catch (err) {
      window.showToast(`Analysis failed: ${err.message}`, "error");
    }
  },

  async loadConflicts() {
    const tbody = document.getElementById("conflicts-tbody");
    if (!tbody) return;

    const search = document.getElementById("conflict-search-input")?.value.trim() || "";
    const severity = document.getElementById("conflict-filter-severity")?.value || "all";
    const conflictType = document.getElementById("conflict-filter-type")?.value || "all";
    const docId = document.getElementById("conflict-filter-doc")?.value || "all";

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (severity !== "all") params.append("severity", severity);
    if (conflictType !== "all") params.append("conflict_type", conflictType);
    if (docId !== "all") params.append("document_id", docId);

    try {
      this.conflictsList = await API.get(`/api/conflicts?${params.toString()}`);

      if (this.conflictsList.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; color: var(--text-dim); padding: 48px;">
              No conflicts or overlaps match your filter criteria.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = this.conflictsList.map(c => {
        let typeBadgeClass = 'badge-partial';
        const tLower = c.conflict_type.toLowerCase();
        if (tLower.includes('contra')) typeBadgeClass = 'badge-contradiction';
        else if (tLower.includes('over')) typeBadgeClass = 'badge-overlap';
        else if (tLower.includes('dup')) typeBadgeClass = 'badge-duplicate';
        else if (tLower.includes('ambig')) typeBadgeClass = 'badge-ambiguity';

        return `
          <tr>
            <td>
              <span class="ref-tag" onclick="window.Comparison?.openModal('${c.conflict_id}')">${c.conflict_id.substring(0, 8)}</span>
            </td>
            <td>
              <span class="ref-tag" onclick="window.App?.jumpToRequirement('${c.requirement_1.requirement_id}')">${c.requirement_1.reference_code}</span>
              <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;">
                ${c.requirement_1.source_document} ${c.requirement_1.page_number ? `(p.${c.requirement_1.page_number})` : ''}
              </div>
            </td>
            <td>
              <span class="ref-tag" onclick="window.App?.jumpToRequirement('${c.requirement_2.requirement_id}')">${c.requirement_2.reference_code}</span>
              <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 2px;">
                ${c.requirement_2.source_document} ${c.requirement_2.page_number ? `(p.${c.requirement_2.page_number})` : ''}
              </div>
            </td>
            <td><span class="badge ${typeBadgeClass}">${c.conflict_type}</span></td>
            <td><span class="badge badge-${c.severity.toLowerCase()}">${c.severity}</span></td>
            <td style="max-width: 320px; font-size: 0.84rem; line-height: 1.45; color: var(--text-main);">
              <div style="font-weight: 500;">${c.explanation}</div>
              ${c.conflicting_elements ? `<div style="font-size: 0.76rem; color: #fca5a5; margin-top: 4px;">• ${c.conflicting_elements}</div>` : ''}
            </td>
            <td style="font-size: 0.78rem; color: var(--text-muted); white-space: nowrap;">
              <div>${c.requirement_1.source_document}</div>
              <div style="color: var(--text-dim);">vs ${c.requirement_2.source_document}</div>
            </td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="window.Comparison?.openModal('${c.conflict_id}')">
                <i data-lucide="split" style="width: 14px; height: 14px;"></i>
                <span>Inspect</span>
              </button>
            </td>
          </tr>
        `;
      }).join("");

      lucide.createIcons();
    } catch (err) {
      console.error("Failed to load conflicts:", err);
    }
  }
};

window.Conflicts = Conflicts;
