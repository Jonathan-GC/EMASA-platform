<template>
  <div class="google-login">
    <button
      type="button"
      class="google-btn"
      :disabled="loading"
      @click="onClick"
    >
      <svg viewBox="0 0 48 48" width="20" height="20" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
        <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
      </svg>
      <span>{{ loading ? 'Conectando…' : 'Continuar con Google' }}</span>
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Capacitor } from '@capacitor/core'
import API from '@/utils/api/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)
const error = ref(null)

const APP_URL = import.meta.env.VITE_APP_URL || (typeof window !== 'undefined' ? window.location.origin : '')

function navigateAfterLogin() {
  const explicit = route.query.next
  if (explicit) { router.replace(String(explicit)); return }
  if (auth.needsTenantSetup) router.replace('/tenant-setup')
  else if (auth.isSuperUser || auth.isGlobalUser) router.replace('/tenants')
  else router.replace('/home')
}

async function signInWeb() {
  // 1. Ask the backend for the Google consent URL.
  const resp = await API.get(API.GOOGLE_LOGIN_URL)
  const payload = Array.isArray(resp) ? resp[0] : resp
  const googleUrl = payload?.url
  if (!googleUrl) throw new Error('Backend no devolvió una URL válida.')

  // 2. Stamp a `state` query into the Google URL so the callback view
  // knows where to send the user after login (?next=...).
  const state = encodeURIComponent(JSON.stringify({
    next: route.query.next || null,
  }))
  const u = new URL(googleUrl)
  u.searchParams.set('redirect_uri', `${APP_URL}/auth/callback`)
  u.searchParams.set('state', `${APP_URL}/auth/callback|${state}`)
  const finalUrl = u.toString()

  if (Capacitor.isNativePlatform()) {
    // Native: open the system browser, which handles the OAuth flow.
    // Backend's GOOGLE_REDIRECT_URI is configured server-side and will
    // land on the SPA's /auth/callback view on web. For Android a
    // deep-link redirect_uri would need to be added to the backend.
    const { Browser } = await import('@capacitor/browser')
    await Browser.open({ url: finalUrl })
    return
  }
  window.location.href = finalUrl
}

async function onClick() {
  error.value = null
  loading.value = true
  try {
    await signInWeb()
  } catch (e) {
    error.value = e?.message || 'No se pudo iniciar el login con Google'
    loading.value = false
  }
}
</script>

<style scoped>
.google-login {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
  width: 100%;
}
.google-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border: 1px solid #dadce0;
  border-radius: 4px;
  background: #fff;
  color: #3c4043;
  font-weight: 500;
  font-size: 0.95rem;
  cursor: pointer;
  width: 100%;
  max-width: 320px;
  transition: background 120ms ease;
}
.google-btn:hover:not(:disabled) { background: #f8f9fa; }
.google-btn:disabled { opacity: 0.7; cursor: progress; }
.error { color: #c0392b; font-size: 0.9rem; margin: 0; }
</style>
