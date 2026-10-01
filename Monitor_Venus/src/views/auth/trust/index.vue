<template>
  <ion-page>
    <ion-content
      :fullscreen="true"
      class="h-full ion-no-padding"
      :scroll-y="isMobile"
    >
      <div class="login-background min-h-screen">
        <div class="content-center min-h-full header-container">
          <img :src="MonitorLogo" alt="Monitor Logo" class="logo">
        </div>
        <div class="trust-card-container">
          <ion-card class="form-card">
            <ion-card-header>
              <ion-card-title class="form-card-title">Confía en este dispositivo</ion-card-title>
              <ion-card-subtitle class="form-card-subtitle">
                {{ subtitle }}
              </ion-card-subtitle>
            </ion-card-header>

            <ion-card-content>
              <!-- Estado inicial: eligiendo -->
              <template v-if="!loading">
                <div class="device-banner">
                  <ion-icon :icon="icons.phone_portrait"></ion-icon>
                  <div class="device-banner-text">
                    <span class="device-banner-label">Dispositivo actual</span>
                    <span class="device-banner-name">{{ deviceName }}</span>
                  </div>
                </div>

                <p class="trust-explanation">{{ explanation }}</p>

                <ion-item lines="none" class="remember-item">
                  <ion-checkbox
                    slot="start"
                    :checked="remember"
                    color="warning"
                    class="trust-checkbox"
                    @ionChange="onRememberChange"
                  ></ion-checkbox>
                  <ion-label class="remember-label">
                    No volver a preguntar en este dispositivo
                  </ion-label>
                </ion-item>
              </template>

              <!-- Aviso de error -->
              <ion-item v-if="error" lines="none" class="error-item">
                <ion-label color="danger">
                  <ion-icon :icon="icons.alertCircle"></ion-icon>
                  {{ error }}
                </ion-label>
              </ion-item>

              <div class="button-container">
                <ion-button
                  expand="block"
                  class="trust-button-primary"
                  :disabled="loading"
                  @click="submit(true)"
                >
                  <ion-icon :icon="icons.shield" slot="start"></ion-icon>
                  Confiar en este dispositivo
                </ion-button>

                <ion-button
                  expand="block"
                  fill="outline"
                  color="medium"
                  :disabled="loading"
                  @click="submit(false)"
                >
                  <ion-icon :icon="icons.key" slot="start"></ion-icon>
                  Solo esta vez
                </ion-button>
              </div>
            </ion-card-content>
          </ion-card>
        </div>
        <AuthFooter />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { useOtpStore } from '@/stores/otpStore.js'
import API from '@/utils/api/api.js'
import { paths } from '@/plugins/router/paths.js'
import tokenManager from '@/utils/auth/tokenManager.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import MonitorLogo from '@assets/monitor_logo_dark.svg'
import {
  getCurrentDeviceName,
  getTrustDevicePreference,
  setTrustDevicePreference
} from '@/utils/auth/deviceTrust.js'

const router = useRouter()
const authStore = useAuthStore()
const otpStore = useOtpStore()

const icons = inject('icons', {})

const { isMobile } = useResponsiveView(768)

const loading = ref(false)
const error = ref(null)
const remember = ref(false)
// Se marca al aceptar la decisión para poder navegar sin que el guard de salida
// bloquee la redirección final.
const decided = ref(false)

// La pantalla es obligatoria: se bloquea la salida salvo hacia las rutas donde
// el usuario ya está autenticado ( redirección final, arranque ) o al login.
const ALLOWED_EXIT_PATHS = new Set([
  paths.HOME,
  paths.TENANTS,
  paths.TENANT_SETUP,
  paths.LOGIN
])

onBeforeRouteLeave((to) => {
  if (loading.value || decided.value) return true
  return ALLOWED_EXIT_PATHS.has(to.path)
})

const deviceName = computed(() => getCurrentDeviceName())
const ttlDays = computed(() => otpStore.deviceTrustTtlDays)

const subtitle = computed(() =>
  'Elige si quieres que recordemos este dispositivo para tu próxima entrada.'
)

const explanation = computed(() => {
  const days = ttlDays.value
  if (!Number.isFinite(days) || days <= 0) {
    return 'Si confías en este dispositivo podemos saltarnos la verificación en los próximos ingresos.'
  }
  return `Si confías en este dispositivo podemos saltarnos la verificación durante los próximos ${days} días.`
})

// Redirige según el estado del usuario (misma lógica que el login)
const navigateAfterLogin = () => {
  otpStore.clearPendingLogin()
  if (authStore.needsTenantSetup) {
    router.replace(paths.TENANT_SETUP)
  } else if (authStore.isSuperUser || authStore.isGlobalUser) {
    router.replace(paths.TENANTS)
  } else {
    router.replace(paths.HOME)
  }
}

// POST /users/sessions/trust_current/
const submit = async (trust) => {
  if (loading.value) return
  loading.value = true
  error.value = null

  try {
    if (!API.getCookieValue('csrftoken')) {
      await API.get(API.CSRF_TOKEN)
    }

    await API.post(API.SESSIONS_TRUST_CURRENT, { trust })

    // Solo se guarda la preferencia si el usuario lo pidió explícitamente
    if (remember.value) {
      setTrustDevicePreference(trust ? 'always' : 'never')
    }

    decided.value = true
    otpStore.clearTrustDecision()
    navigateAfterLogin()
  } catch (err) {
    console.error('❌ Error guardando la confianza del dispositivo:', err)

    const msg = err?.message || ''
    // La sesión pudo ser revocada en otra pestaña/dispositivo mientras el
    // usuario decidía: en ese caso no hay nada que reintentar aquí.
    const sessionGone =
      msg.includes('SESSION_INVALID') ||
      msg.includes('Session has been revoked') ||
      msg.includes('Active session for current device not found')

    if (sessionGone) {
      error.value = '❌ Esta sesión ya no está activa. Inicia sesión nuevamente.'
      loading.value = false
      setTimeout(() => {
        authStore.logout()
        router.replace(paths.LOGIN)
      }, 2500)
      return
    }

    error.value = '❌ No se pudo guardar tu preferencia. Inténtalo de nuevo.'
    loading.value = false
  }
}

const onRememberChange = (e) => {
  remember.value = Boolean(e?.detail?.checked ?? e?.target?.checked)
}

onMounted(() => {
  // Al entrar por URL directa o tras recargar la WebView, el store Pinia puede
  // haberse perdido: se intenta recuperar el flag persistido.
  if (!otpStore.trustDecisionRequired) {
    otpStore.restoreTrustDecision()
  }

  // Sin una decisión pendiente no hay nada que decidir aquí. Si el usuario ya
  // está autenticado (p. ej. recarga tardía) se va directo a su destino en vez
  // de pasar por el login.
  if (!otpStore.trustDecisionRequired) {
    otpStore.clearPendingLogin()
    if (tokenManager.hasValidToken()) {
      navigateAfterLogin()
    } else {
      router.replace(paths.LOGIN)
    }
    return
  }

  // El checkbox arranca marcado si el usuario ya pidió no preguntar antes; si
  // nunca ha decidido, arranca libre.
  remember.value = getTrustDevicePreference() !== null
})
</script>

<style scoped>
.login-background {
  min-height: 100vh;
  background: url('/login.png') no-repeat center center / cover;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  width: auto;
}

.trust-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 1rem;
}

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5rem 1rem 2rem;
}

.form-card {
  max-width: 560px;
  width: 100%;
  margin: 0;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.form-card-title {
  text-align: center;
  font-weight: 600;
}

.form-card-subtitle {
  text-align: center;
}

.device-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-radius: 10px;
  background: var(--ion-color-light, #f4f4f5);
}

.device-banner ion-icon {
  color: var(--ion-color-warning);
  font-size: 24px;
  flex-shrink: 0;
}

.device-banner-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.device-banner-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.7;
}

.device-banner-name {
  font-size: 1rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.trust-explanation {
  margin: 0 0 8px;
  line-height: 1.45;
}

.trust-button-primary {
  --color: #ffffff;
  --background: #000000;
  --background-activated: #1a1a1a;
  --background-hover: #111111;
  --ripple-color: rgba(255, 255, 255, 0.2);
}

.trust-button-primary::part(native) {
  color: #ffffff;
}

.trust-button-primary ion-icon {
  color: #ffffff;
}

.trust-checkbox {
  --checkbox-background-checked: var(--ion-color-warning);
  --checkmark-color: #ffffff;
}

.trust-checkbox[aria-checked="true"]::part(container),
.trust-checkbox[checked]::part(container),
.trust-checkbox.ion-checked::part(container) {
  border-color: var(--ion-color-warning);
}

.remember-item {
  --padding-start: 0;
  --inner-padding-end: 0;
  --background: transparent;
  margin-bottom: 8px;
}

.remember-label {
  font-size: 0.9rem;
}

.button-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.error-item {
  --background: transparent;
  --padding-start: 0;
  --inner-padding-end: 0;
  margin-top: 8px;
}
</style>