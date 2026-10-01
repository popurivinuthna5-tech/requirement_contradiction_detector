// Firebase Configuration & Initialization
window.firebaseConfig = {
  apiKey: "",
  authDomain: "requirement-analyzer-demo.firebaseapp.com",
  projectId: "requirement-analyzer-demo",
  storageBucket: "requirement-analyzer-demo.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef123456"
};

// Check if Firebase is available
window.hasLiveFirebaseConfig = false;

try {
  if (typeof firebase !== 'undefined' && firebase.initializeApp) {
    if (window.firebaseConfig.apiKey) {
      firebase.initializeApp(window.firebaseConfig);
      window.hasLiveFirebaseConfig = true;
      console.log("[Firebase] Live Firebase SDK initialized.");
    } else {
      console.log("[Firebase] Running in Hybrid/Interactive Demo Mode (Google/Apple login ready for project credentials).");
    }
  }
} catch (e) {
  console.warn("[Firebase] Init error (running in fallback mode):", e);
}
