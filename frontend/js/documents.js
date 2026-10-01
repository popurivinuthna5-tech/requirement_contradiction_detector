// Documents Management and Upload Controller

const Documents = {
  documentsList: [],

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-upload-input");
    const quickUploadBtn = document.getElementById("btn-quick-upload");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      quickUploadBtn?.addEventListener("click", () => {
        window.App?.navigateTo("documents");
        fileInput.click();
      });

      fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
          this.handleFiles(Array.from(e.target.files));
          fileInput.value = "";
        }
      });

      // Drag and drop
      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.add("drag-over");
        }, false);
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.remove("drag-over");
        }, false);
      });

      dropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          this.handleFiles(Array.from(dt.files));
        }
      }, false);
    }
  },

  async handleFiles(files) {
    for (const file of files) {
      const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
      if (!['.pdf', '.docx', '.txt'].includes(ext)) {
        window.showToast(`File '${file.name}' is unsupported. Only PDF, DOCX, and TXT are allowed.`, "error");
        continue;
      }

      if (file.size > 25 * 1024 * 1024) {
        window.showToast(`File '${file.name}' exceeds maximum 25 MB limit.`, "error");
        continue;
      }

      try {
        window.showToast(`Uploading and extracting: ${file.name}...`, "info");
        const doc = await API.uploadFile("/api/documents/upload", file);
        window.showToast(`Extracted ${doc.requirement_count} requirements from ${file.name}!`, "success");
      } catch (err) {
        window.showToast(`Upload failed for ${file.name}: ${err.message}`, "error");
      }
    }

    // Refresh view
    await this.loadDocuments();
    await window.Dashboard?.loadSummary();
    await window.Requirements?.loadRequirements();
  },

  async loadDocuments() {
    const tbody = document.getElementById("documents-tbody");
    if (!tbody) return;

    try {
      this.documentsList = await API.get("/api/documents");
      const badge = document.getElementById("doc-count-badge");
      if (badge) badge.textContent = `${this.documentsList.length} Documents`;

      // Update document dropdown filters across tabs
      this.updateDocumentDropdowns();

      if (this.documentsList.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-dim); padding: 36px;">
              No requirement documents uploaded yet. Upload a PDF, DOCX, or TXT document above.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = this.documentsList.map(doc => `
        <tr>
          <td>
            <div style="font-weight: 600; color: #fff;">${doc.original_filename}</div>
            <div style="font-size: 0.72rem; color: var(--text-dim);">${(doc.file_size / 1024).toFixed(1)} KB</div>
          </td>
          <td><span class="format-pill">${doc.document_type.toUpperCase().replace('.', '')}</span></td>
          <td style="color: var(--text-muted); font-size: 0.84rem;">${doc.upload_date}</td>
          <td>
            <span class="ref-tag" style="background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border-color: rgba(16, 185, 129, 0.3);">
              ${doc.requirement_count} Requirements
            </span>
          </td>
          <td>
            <span class="badge ${doc.status === 'completed' || doc.status === 'uploaded' ? 'badge-low' : (doc.status === 'failed' ? 'badge-critical' : 'badge-medium')}">
              ${doc.status}
            </span>
          </td>
          <td>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary btn-sm" onclick="window.App?.jumpToDocRequirements('${doc.document_id}')" title="View Requirements">
                <i data-lucide="eye" style="width: 14px; height: 14px;"></i>
              </button>
              <button class="btn btn-danger btn-sm" onclick="window.Documents?.deleteDocument('${doc.document_id}')" title="Delete Document">
                <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
              </button>
            </div>
          </td>
        </tr>
      `).join("");

      lucide.createIcons();
    } catch (err) {
      console.error("Failed to list documents:", err);
    }
  },

  updateDocumentDropdowns() {
    const docSelects = [
      document.getElementById("req-filter-doc"),
      document.getElementById("conflict-filter-doc")
    ];

    docSelects.forEach(select => {
      if (!select) return;
      const currentVal = select.value;
      let opts = '<option value="all">All Documents</option>';
      this.documentsList.forEach(d => {
        opts += `<option value="${d.document_id}">${d.original_filename}</option>`;
      });
      select.innerHTML = opts;
      select.value = currentVal || "all";
    });
  },

  async deleteDocument(docId) {
    if (!confirm("Are you sure you want to delete this document and all its extracted requirements and conflicts?")) {
      return;
    }

    try {
      await API.delete(`/api/documents/${docId}`);
      window.showToast("Document deleted successfully.", "info");
      await this.loadDocuments();
      await window.Dashboard?.loadSummary();
      await window.Requirements?.loadRequirements();
      await window.Conflicts?.loadConflicts();
    } catch (err) {
      window.showToast(`Delete failed: ${err.message}`, "error");
    }
  }
};

window.Documents = Documents;
