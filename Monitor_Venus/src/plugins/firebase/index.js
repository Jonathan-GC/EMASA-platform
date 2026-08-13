// src/plugins/firebase.js
// Firebase is only used for push notifications (after authentication),
// so the SDK is lazy-loaded to keep it out of the app entry chunk.

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

let appInstance = null

export async function ensureFirebaseApp() {
  if (appInstance) return appInstance
  const { initializeApp } = await import('firebase/app')
  appInstance = initializeApp(firebaseConfig)
  return appInstance
}