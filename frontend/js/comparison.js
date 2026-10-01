// Side-by-Side Requirement Comparison Modal Controller (Sections 7 & 8)

const Comparison = {
  currentConflict: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const modal = document.getElementById("comparison-modal");
    const closeBtn = document.getElementById("btn-close-comparison-modal");

    closeBtn?.addEventListener("click", () => this.closeModal());
    
    // Close on backdrop click
    modal?.addEventListener("click", (e) => {
      if (e.target === modal) this.closeModal();
    });

    // Close on ESC key
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal?.classList.contains("active")) {
        this.closeModal();
      }
    });
  },

  async openModal(conflictId) {
    try {
      const conflict = await API.get(`/api/conflicts/${conflictId}`);
      this.currentConflict = conflict;
      this.populateModal(conflict);

      const modal = document.getElementById("comparison-modal");
      if (modal) modal.classList.add("active");
      lucide.createIcons();
    } catch (err) {
      console.error("Failed to fetch conflict details:", err);
      window.showToast("Failed to load conflict details", "error");
    }
  },

  closeModal() {
    const modal = document.getElementById("comparison-modal");
    if (modal) modal.classList.remove("active");
  },

  populateModal(c) {
    // Header
    const idEl = document.getElementById("modal-conflict-id");
    const typeEl = document.getElementById("modal-conflict-type");
    const sevBadge = document.getElementById("modal-severity-badge");

    if (idEl) idEl.textContent = c.conflict_id.substring(0, 10);
    if (typeEl) typeEl.textContent = c.conflict_type;
    if (sevBadge) {
      sevBadge.textContent = c.severity;
      sevBadge.className = `badge badge-${c.severity.toLowerCase()}`;
    }

    // LEFT Requirement 1
    const req1 = c.requirement_1;
    document.getElementById("modal-req1-ref").textContent = req1.reference_code;
    document.getElementById("modal-req1-ref").onclick = () => {
      this.closeModal();
      window.App?.jumpToRequirement(req1.requirement_id);
    };
    document.getElementById("modal-req1-type").textContent = req1.requirement_type;
    document.getElementById("modal-req1-doc").textContent = req1.source_document;
    document.getElementById("modal-req1-sec").textContent = req1.section || "General";
    document.getElementById("modal-req1-page").textContent = req1.page_number ? `Page ${req1.page_number}` : "Unavailable";
    document.getElementById("modal-req1-text").textContent = `"${req1.requirement_text}"`;

    // RIGHT Requirement 2
    const req2 = c.requirement_2;
    document.getElementById("modal-req2-ref").textContent = req2.reference_code;
    document.getElementById("modal-req2-ref").onclick = () => {
      this.closeModal();
      window.App?.jumpToRequirement(req2.requirement_id);
    };
    document.getElementById("modal-req2-type").textContent = req2.requirement_type;
    document.getElementById("modal-req2-doc").textContent = req2.source_document;
    document.getElementById("modal-req2-sec").textContent = req2.section || "General";
    document.getElementById("modal-req2-page").textContent = req2.page_number ? `Page ${req2.page_number}` : "Unavailable";
    document.getElementById("modal-req2-text").textContent = `"${req2.requirement_text}"`;

    // Details Breakdown below
    document.getElementById("modal-explanation").textContent = c.explanation;
    document.getElementById("modal-conflicting-elements").textContent = c.conflicting_elements || "Differing specification conditions.";
    document.getElementById("modal-suggested-clarification").textContent = c.suggested_clarification || "Harmonize specification definitions across teams.";
  }
};

window.Comparison = Comparison;
