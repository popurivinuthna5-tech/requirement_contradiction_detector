// Settings and AI Provider Controller

const Settings = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById("btn-save-ai-settings")?.addEventListener("click", () => this.saveAISettings());
  },

  async loadSettings() {
    try {
      const data = await API.get("/api/settings/ai");
      const select = document.getElementById("settings-ai-provider");
      if (select && data.active_provider) {
        select.value = data.active_provider;
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  },

  async saveAISettings() {
    const select = document.getElementById("settings-ai-provider");
    const provider = select?.value || "local";

    try {
      await API.post("/api/settings/ai", {
        provider_name: provider
      });
      window.showToast(`AI provider successfully updated to '${provider}'`, "success");
    } catch (err) {
      window.showToast(`Failed to update AI settings: ${err.message}`, "error");
    }
  }
};

window.Settings = Settings;
