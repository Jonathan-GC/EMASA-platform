<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="callback-page">
        <div class="header-container">
          <img src="/monitor_logo.svg" alt="Monitor Logo" class="logo" />
        </div>

        <div class="callback-card-container">
          <ion-card class="callback-card">
            <ion-card-content class="card-content">
              <template v-if="!error">
                <div class="icon-container">
                  <ion-spinner name="crescent" class="orange-spinner"></ion-spinner>
                </div>
                <h1 class="callback-title">Conectando con tu cuenta…</h1>
                <p class="callback-message">{{ loadingMessage }}</p>
              </template>
              <template v-else>
                <div class="icon-container">
                  <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
                </div>
                <h1 class="callback-title">Algo salió mal</h1>
                <p class="callback-error">{{ error }}</p>
                <ion-button expand="block" color="primary" class="continue-button" @click="goToLoginWithError(error)">
                  Volver al login
                </ion-button>
              </template>
            </ion-card-content>
          </ion-card>
        </div>

        <div class="footer-band">
          <AuthFooter />
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import API from '@/utils/api/api'
import { parseGoogleState, postGoogleLinkCode } from '@/utils/auth/googleOAuth'
import AuthFooter from '@/components/layout/AuthFooter.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const icons = inject('icons', {})
const error = ref(null)

const loadingMessages = [
  'Conectando con tu cuenta de forma segura…',
  'Verificando tu identidad…',
  'Casi listo, un momento…',
]
const loadingMessage = ref(loadingMessages[0])
let loadingTimer = null

function startLoadingMessages() {
  let index = 0
  loadingTimer = setInterval(() => {
    index = (index + 1) % loadingMessages.length
    loadingMessage.value = loadingMessages[index]
  }, 1500)
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function ensureCsrfCookie() {
  if (API.getCookieValue('csrftoken')) return

  const response = await fetch(`${API.API_BASE_URL}${API.CSRF_TOKEN}`, {
    method: 'GET',
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`No se pudo preparar CSRF (${response.status}).`)
  }
}

async function postGoogleCallback(code) {
  await ensureCsrfCookie()
  const csrfToken = API.getCookieValue('csrftoken')

  const response = await fetch(`${API.API_BASE_URL}${API.GOOGLE_CALLBACK}`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
    },
    body: JSON.stringify({ code }),
  })

  let payload = null
  const text = await response.text()
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = { detail: text }
    }
  }

  if (!response.ok) {
    const detail = payload?.detail || payload?.error || response.statusText || 'Google login failed.'
    const code = payload?.code ? ` (${payload.code})` : ''
    throw new Error(`${detail}${code} [HTTP ${response.status}]`)
  }

  return payload
}

function navigateAfterLogin(next) {
  if (next) { router.replace(String(next)); return }
  if (auth.needsTenantSetup) router.replace('/tenant-setup')
  else if (auth.isSuperUser || auth.isGlobalUser) router.replace('/tenants')
  else router.replace('/home')
}

function goToLoginWithError(message) {
  router.replace({ name: 'login', query: { error: String(message) } })
}

async function handleLink(code, next) {
  try {
    // POST { code } → backend validates the Google identity and attaches
    // a new OAuthAccount to the currently authenticated user.
    await postGoogleLinkCode(code)
    router.replace(next || '/users')
  } catch (e) {
    const message = String(e?.message || '')
    if (message.includes('(409)') || message.includes('email_exists') || message.includes('already exists')) {
      error.value = 'Esta cuenta de Google ya está vinculada a otro usuario.'
    } else {
      error.value = message || 'No se pudo vincular la cuenta de Google.'
    }
  }
}

onMounted(async () => {
  startLoadingMessages()

  // Google redirects the browser here after the user consents. The URL
  // contains ?code=... (success) or ?error=...&error_description=... (failure).
  const code = route.query.code
  const oauthError = route.query.error
  const errorDescription = route.query.error_description

  if (oauthError) {
    error.value = errorDescription || String(oauthError)
    return
  }

  if (!code) {
    error.value = 'No authorization code returned from Google.'
    return
  }

  // The `state` query param is `${redirectUri}|${jsonState}`. We use the
  // JSON portion to remember where to send the user and what to do.
  const state = parseGoogleState(route.query.state)
  const next = state?.next || null
  const mode = state?.mode || 'login'

  if (mode === 'link') {
    await handleLink(code, next)
    return
  }

  try {
    // POST { code } → backend exchanges the code, verifies id_token,
    // finds/creates the user, returns { access } and sets refresh cookie.
    // Google ID tokens can occasionally arrive one clock tick ahead of the
    // backend verifier, so wait briefly before exchanging the one-time code.
    await wait(1500)

    let resp
    try {
      resp = await postGoogleCallback(code)
    } catch (e) {
      if (String(e?.message || '').includes('403')) {
        await fetch(`${API.API_BASE_URL}${API.CSRF_TOKEN}`, {
          method: 'GET',
          credentials: 'include',
        })
        resp = await postGoogleCallback(code)
      } else {
        throw e
      }
    }
    const payload = Array.isArray(resp) ? resp[0] : resp

    if (!payload?.access) {
      throw new Error('Backend no devolvió access token')
    }

    const ok = auth.login(payload.access, payload.refresh || null)
    if (!ok) {
      throw new Error('No se pudo guardar el access token')
    }

    await auth.fetchUserProfile().catch(() => { })
    navigateAfterLogin(next)
  } catch (e) {
    // Handle the 409 case where the email already exists in the system
    // but has no linked Google identity. The frontend should ask the
    // user to log in with their password and link the account later.
    const message = String(e?.message || '')
    if (message.includes('email_exists') || message.includes('already exists')) {
      error.value = 'Ya existe una cuenta con ese correo. Inicia sesión con tu contraseña y vincula Google desde Configuración.'
      return
    }
    error.value = message || 'Error desconocido durante el login con Google.'
  }
})

onBeforeUnmount(() => {
  if (loadingTimer) clearInterval(loadingTimer)
})
</script>

<style scoped>
.callback-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f9fafb;
}

.header-container {
  display: flex;
  justify-content: center;
  padding: 3rem 1rem 2rem;
}

.logo {
  height: 60px;
  width: auto;
}

.callback-card-container {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 0 1rem 2rem;
}

.callback-card {
  width: 100%;
  max-width: 440px;
  margin: 0;
  border-radius: 16px;
  box-shadow: none;
  background-color: #f9fafb;
}

.card-content {
  padding: 2.5rem 2rem;
  text-align: center;
}

.icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.orange-spinner {
  --color: #ee731b;
  width: 56px;
  height: 56px;
}

.callback-title {
  margin: 0 0 0.5rem;
  font-size: 1.4rem;
  font-weight: 700;
  color: #111827;
}

.callback-message {
  margin: 0;
  font-size: 0.95rem;
  color: #6b7280;
}

.callback-error {
  margin: 0;
  padding: 0.75rem;
  border-left: 3px solid var(--ion-color-danger);
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  font-size: 0.9rem;
  color: #c0392b;
  text-align: left;
}

.continue-button {
  margin-top: 1rem;
  font-weight: 600;
}

.footer-band {
  background: #111827;
}

@media (max-width: 768px) {
  .header-container {
    padding: 2rem 1rem 1.5rem;
  }

  .logo {
    height: 48px;
  }

  .card-content {
    padding: 2rem 1.25rem;
  }

  .orange-spinner {
    width: 48px;
    height: 48px;
  }
}
</style>
