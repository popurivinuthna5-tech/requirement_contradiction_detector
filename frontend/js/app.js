// Main Application Coordinator & Routing

const App = {
  currentPage: "dashboard",

  init() {
    this.bindNavigation();
    
    // Initialize modular controllers
    window.Auth?.init();
    window.Dashboard?.init();
    window.Documents?.init();
    window.Requirements?.init();
    window.Conflicts?.init();
    window.Comparison?.init();
    window.Reports?.init();
    window.Settings?.init();

    // Render icons
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  },

  bindNavigation() {
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        const page = link.getAttribute("data-page");
        if (page) this.navigateTo(page);
      });
    });
  },

  navigateTo(pageId) {
    this.currentPage = pageId;

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach(link => {
      link.classList.toggle("active", link.getAttribute("data-page") === pageId);
    });

    // Update page title in topbar
    const titleEl = document.getElementById("topbar-page-title");
    const titles = {
      dashboard: "Dashboard Overview",
      documents: "Requirement Documents",
      requirements: "Requirements Explorer",
      conflicts: "Semantic Conflict Analysis",
      reports: "Conflict Audit Reports",
      settings: "System Configuration"
    };
    if (titleEl) titleEl.textContent = titles[pageId] || "ReqConflict AI";

    // Show active page view
    document.querySelectorAll(".page-view").forEach(view => {
      view.classList.toggle("active", view.id === `view-${pageId}`);
    });

    // Refresh view specific data
    if (pageId === "dashboard") window.Dashboard?.loadSummary();
    else if (pageId === "documents") window.Documents?.loadDocuments();
    else if (pageId === "requirements") window.Requirements?.loadRequirements();
    else if (pageId === "conflicts") window.Conflicts?.loadConflicts();
    else if (pageId === "reports") window.Reports?.loadReport();
    else if (pageId === "settings") window.Settings?.loadSettings();

    lucide.createIcons();
  },

  onUserAuthenticated() {
    this.navigateTo(this.currentPage);
  },

  jumpToRequirement(reqId) {
    this.navigateTo("requirements");
    setTimeout(() => {
      window.Requirements?.loadRequirements(reqId);
    }, 100);
  },

  jumpToDocRequirements(docId) {
    this.navigateTo("requirements");
    setTimeout(() => {
      const select = document.getElementById("req-filter-doc");
      if (select) {
        select.value = docId;
        window.Requirements?.loadRequirements();
      }
    }, 100);
  }
};

// Global helper functions
window.navigateTo = (page) => App.navigateTo(page);
window.triggerAnalysis = () => window.Conflicts?.triggerAnalysis();

window.showToast = function(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  let iconName = "info";
  if (type === "success") iconName = "check-circle-2";
  else if (type === "error") iconName = "alert-circle";

  toast.innerHTML = `
    <i data-lucide="${iconName}" style="width: 18px; height: 18px; flex-shrink: 0;"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 300);
  }, 4500);
};

window.App = App;

// Bootstrap on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
