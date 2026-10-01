// Requirements Registry and Search Controller

const Requirements = {
  requirementsList: [],

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const searchInput = document.getElementById("req-search-input");
    const docFilter = document.getElementById("req-filter-doc");
    const typeFilter = document.getElementById("req-filter-type");

    let debounceTimer;
    searchInput?.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => this.loadRequirements(), 250);
    });

    docFilter?.addEventListener("change", () => this.loadRequirements());
    typeFilter?.addEventListener("change", () => this.loadRequirements());
  },

  async loadRequirements(highlightId = null) {
    const tbody = document.getElementById("requirements-tbody");
    if (!tbody) return;

    const search = document.getElementById("req-search-input")?.value.trim() || "";
    const docId = document.getElementById("req-filter-doc")?.value || "all";
    const reqType = document.getElementById("req-filter-type")?.value || "all";

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (docId !== "all") params.append("document_id", docId);
    if (reqType !== "all") params.append("req_type", reqType);

    try {
      this.requirementsList = await API.get(`/api/requirements?${params.toString()}`);

      if (this.requirementsList.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align: center; color: var(--text-dim); padding: 36px;">
              No matching requirements found.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = this.requirementsList.map(r => {
        const isHighlight = highlightId && (r.requirement_id === highlightId || r.reference_code === highlightId);
        return `
          <tr id="req-row-${r.requirement_id}" style="${isHighlight ? 'background-color: rgba(99, 102, 241, 0.18); border-left: 3px solid var(--accent-primary);' : ''}">
            <td><span class="ref-tag">${r.reference_code}</span></td>
            <td>
              <div style="font-weight: 600; color: #fff; font-size: 0.84rem;">${r.document_name || 'Document'}</div>
            </td>
            <td style="color: var(--text-muted); font-size: 0.82rem; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              ${r.section || 'General'}
            </td>
            <td style="color: var(--text-dim); font-size: 0.82rem;">${r.page_number ? `Page ${r.page_number}` : 'N/A'}</td>
            <td><span class="badge badge-low" style="font-size: 0.7rem;">${r.requirement_type}</span></td>
            <td>
              <span class="badge ${r.priority.toLowerCase().includes('high') || r.priority.toLowerCase().includes('must') ? 'badge-critical' : (r.priority.toLowerCase().includes('medium') ? 'badge-medium' : 'badge-low')}">
                ${r.priority}
              </span>
            </td>
            <td style="color: var(--text-main); font-size: 0.88rem; line-height: 1.5; max-width: 480px;">
              ${r.requirement_text}
            </td>
          </tr>
        `;
      }).join("");

      if (highlightId) {
        const targetRow = document.getElementById(`req-row-${highlightId}`);
        targetRow?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

    } catch (err) {
      console.error("Failed to load requirements:", err);
    }
  }
};

window.Requirements = Requirements;
