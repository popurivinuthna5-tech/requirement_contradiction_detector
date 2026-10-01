// Authentication State & Provider Handling

const Auth = {
  currentUser: null,

  init() {
    this.bindEvents();
    this.checkSession();
  },

  bindEvents() {
    document.getElementById("btn-login-google")?.addEventListener("click", () => this.loginWithGoogle());
    document.getElementById("btn-login-apple")?.addEventListener("click", () => this.loginWithApple());
    document.getElementById("btn-login-demo")?.addEventListener("click", () => this.loginWithDemo());
    document.getElementById("btn-logout")?.addEventListener("click", () => this.logout());
  },

  async checkSession() {
    const savedToken = localStorage.getItem("req_auth_token");
    const savedUserJson = localStorage.getItem("req_auth_user");

    if (savedToken && savedUserJson) {
      try {
        this.currentUser = JSON.parse(savedUserJson);
        // Verify with backend
        const profile = await API.get("/api/auth/me");
        this.currentUser = profile;
        this.updateUI();
        this.hideAuthModal();
        window.App?.onUserAuthenticated();
        return;
      } catch (err) {
        console.warn("Session validation failed, resetting session:", err);
        this.handleUnauthenticated();
      }
    } else {
      this.handleUnauthenticated();
    }
  },

  async loginWithGoogle() {
    try {
      window.showToast("Initiating Google Authentication...", "info");
      
      // If live Firebase credentials configured
      if (window.hasLiveFirebaseConfig && typeof firebase !== 'undefined') {
        const provider = new firebase.auth.GoogleAuthProvider();
        const result = await firebase.auth().signInWithPopup(provider);
        const token = await result.user.getIdToken();
        await this.handleSuccessfulAuth(token, result.user.uid, result.user.email, result.user.displayName, "google");
      } else {
        // Fallback demo/interactive Google Auth
        const simulatedUserId = "google_user_" + Math.random().toString(36).substring(2, 9);
        const token = "demo-token-" + simulatedUserId;
        await this.handleSuccessfulAuth(token, simulatedUserId, "lead.architect@enterprise.org", "Alex Chen (Google)", "google");
      }
    } catch (err) {
      console.error("Google Auth failed:", err);
      window.showToast(`Google Sign-In failed: ${err.message}`, "error");
    }
  },

  async loginWithApple() {
    try {
      window.showToast("Initiating Apple Authentication...", "info");
      
      // If live Firebase credentials configured
      if (window.hasLiveFirebaseConfig && typeof firebase !== 'undefined') {
        const provider = new firebase.auth.OAuthProvider('apple.com');
        const result = await firebase.auth().signInWithPopup(provider);
        const token = await result.user.getIdToken();
        await this.handleSuccessfulAuth(token, result.user.uid, result.user.email, result.user.displayName, "apple");
      } else {
        // Fallback demo/interactive Apple Auth
        const simulatedUserId = "apple_user_" + Math.random().toString(36).substring(2, 9);
        const token = "demo-token-" + simulatedUserId;
        await this.handleSuccessfulAuth(token, simulatedUserId, "sarah.lead@appleid.corp", "Sarah Miller (Apple)", "apple");
      }
    } catch (err) {
      console.error("Apple Auth failed:", err);
      window.showToast(`Apple Sign-In failed: ${err.message}`, "error");
    }
  },

  async loginWithDemo() {
    try {
      const demoId = "analyst_" + Math.random().toString(36).substring(2, 7);
      const token = "demo-token-" + demoId;
      await this.handleSuccessfulAuth(token, demoId, "demo.analyst@company.com", "Demo Lead Analyst", "demo");
      window.showToast("Signed in as Demo Lead Analyst. Loading sample workspace...", "success");
      await window.Dashboard?.loadDemoData();
    } catch (err) {
      console.error("Demo login error:", err);
      window.showToast("Demo sign-in failed", "error");
    }
  },

  async handleSuccessfulAuth(token, userId, email, displayName, provider) {
    localStorage.setItem("req_auth_token", token);
    
    // Verify with backend
    const verifiedUser = await API.post("/api/auth/verify", {
      id_token: token.startsWith("demo-token-") ? null : token,
      user_id: userId,
      email: email,
      display_name: displayName,
      provider: provider
    });

    this.currentUser = verifiedUser;
    localStorage.setItem("req_auth_user", JSON.stringify(verifiedUser));

    this.updateUI();
    this.hideAuthModal();
    window.showToast(`Welcome, ${verifiedUser.display_name}!`, "success");
    window.App?.onUserAuthenticated();
  },

  updateUI() {
    if (!this.currentUser) return;
    
    const nameEl = document.getElementById("user-name-display");
    const avatarEl = document.getElementById("user-avatar-display");
    const providerEl = document.getElementById("user-provider-display");

    if (nameEl) nameEl.textContent = this.currentUser.display_name || "Analyst";
    if (avatarEl) {
      const initial = (this.currentUser.display_name || "U")[0].toUpperCase();
      avatarEl.innerHTML = `<span>${initial}</span>`;
    }
    if (providerEl) {
      const provName = this.currentUser.provider ? (this.currentUser.provider.charAt(0).toUpperCase() + this.currentUser.provider.slice(1)) : "Verified";
      providerEl.innerHTML = `
        <i data-lucide="shield-check" style="width: 12px; height: 12px;"></i>
        <span>${provName} Auth</span>
      `;
      lucide.createIcons();
    }
  },

  handleUnauthenticated() {
    this.currentUser = null;
    localStorage.removeItem("req_auth_token");
    localStorage.removeItem("req_auth_user");
    this.showAuthModal();
  },

  logout() {
    this.currentUser = null;
    localStorage.removeItem("req_auth_token");
    localStorage.removeItem("req_auth_user");
    if (typeof firebase !== 'undefined' && firebase.auth) {
      try { firebase.auth().signOut(); } catch (e) {}
    }
    window.showToast("Signed out successfully.", "info");
    this.showAuthModal();
  },

  showAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.remove("hidden");
  },

  hideAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.classList.add("hidden");
  }
};

window.Auth = Auth;
