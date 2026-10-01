// API Client with Token Authentication and Error Handling

const API = {
  getToken() {
    return localStorage.getItem("req_auth_token") || "";
  },

  getHeaders(isJson = true) {
    const headers = {};
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (isJson) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  },

  async handleResponse(response) {
    if (response.status === 401) {
      // Session expired or unauthenticated
      window.Auth?.handleUnauthenticated();
      throw new Error("Session expired. Please sign in again.");
    }
    
    if (!response.ok) {
      let errorMsg = `Server error (${response.status})`;
      try {
        const data = await response.json();
        errorMsg = data.detail || errorMsg;
      } catch (e) {
        // Not JSON
      }
      throw new Error(errorMsg);
    }

    // Check if json
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }
    return await response.text();
  },

  async get(url) {
    try {
      const res = await fetch(url, {
        method: "GET",
        headers: this.getHeaders(true)
      });
      return await this.handleResponse(res);
    } catch (err) {
      console.error(`GET ${url} failed:`, err);
      throw err;
    }
  },

  async post(url, data = {}) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: this.getHeaders(true),
        body: JSON.stringify(data)
      });
      return await this.handleResponse(res);
    } catch (err) {
      console.error(`POST ${url} failed:`, err);
      throw err;
    }
  },

  async uploadFile(url, file) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const headers = {};
      const token = this.getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(url, {
        method: "POST",
        headers: headers,
        body: formData
      });
      return await this.handleResponse(res);
    } catch (err) {
      console.error(`Upload to ${url} failed:`, err);
      throw err;
    }
  },

  async delete(url) {
    try {
      const res = await fetch(url, {
        method: "DELETE",
        headers: this.getHeaders(true)
      });
      return await this.handleResponse(res);
    } catch (err) {
      console.error(`DELETE ${url} failed:`, err);
      throw err;
    }
  }
};
