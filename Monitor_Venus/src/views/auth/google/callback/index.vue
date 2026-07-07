<template>
  <div class="callback">
    <p v-if="!error">Finishing sign-in…</p>
    <template v-else>
      <p class="error">{{ error }}</p>
      <button type="button" class="login-link" @click="goToLoginWithError(error)">
        Volver al login
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import API from '@/utils/api/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const error = ref(null)

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

onMounted(async () => {
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
  // JSON portion to remember where to send the user after login.
  let next = null
  const stateParam = route.query.state
  if (stateParam && typeof stateParam === 'string' && stateParam.includes('|')) {
    try {
      const parsed = JSON.parse(decodeURIComponent(stateParam.split('|').slice(1).join('|')))
      next = parsed?.next || null
    } catch {
      // ignore parse errors and fall through to default routing
    }
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

    await auth.fetchUserProfile().catch(() => {})
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
</script>

<style scoped>
.callback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 2rem;
  text-align: center;
}
.error { color: #c0392b; }
.login-link {
  margin-top: 1rem;
  border: 1px solid #dadce0;
  border-radius: 4px;
  background: #fff;
  color: #3c4043;
  cursor: pointer;
  font-weight: 500;
  padding: 0.65rem 1rem;
}
</style>
