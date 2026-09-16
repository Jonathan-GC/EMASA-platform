<template>
    <ion-card class="form-card">
      <ion-card-header class="text-center">
        <ion-card-title>¡Verifica tu identidad!</ion-card-title>
        <ion-card-subtitle>
          Enviamos un código de verificación a
          <strong>{{ identifier }}</strong>
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>{{ loadingText }}</p>
        </div>

        <!-- OTP form -->
        <div v-else>
          <ion-item lines="none" class="otp-item">
            <ion-input-otp
              :value="code"
              length="6"
              inputmode="numeric"
              :disabled="loading"
              :class="{ 'ion-invalid': !!error, 'ion-touched': !!error }"
              class="otp-input"
              @ionInput="onCodeInput"
              @ionBlur="onCodeBlur"
            ></ion-input-otp>
          </ion-item>

          <p class="otp-hint">
            Ingresa el código de 6 dígitos que enviamos a tu correo.
          </p>

          <!-- Error message -->
          <ion-item v-if="error" lines="none" class="error-item">
            <ion-label color="danger">
              <ion-icon :icon="icons.alertCircle"></ion-icon>
              {{ error }}
            </ion-label>
          </ion-item>

          <!-- Success message -->
          <ion-item v-if="success" lines="none" class="success-item">
            <ion-label color="success">
              <ion-icon :icon="icons.checkmark"></ion-icon>
              {{ success }}
            </ion-label>
          </ion-item>

          <!-- Verify button -->
          <div class="button-container">
            <ion-button
              expand="block"
              color="dark"
              :disabled="loading || code.length < 6"
              @click="verify"
            >
              <ion-icon :icon="icons.key" slot="start"></ion-icon>
              Verificar Código
            </ion-button>
          </div>

          <!-- Resend -->
          <div class="resend-container">
            <p class="resend-text">¿No recibiste el código?</p>
            <ion-button
              fill="clear"
              size="small"
              :disabled="resendCooldown > 0 || loading"
              @click="resend"
            >
              <ion-icon :icon="icons.refresh" slot="start"></ion-icon>
              {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : 'Reenviar código' }}
            </ion-button>
          </div>

          <!-- Back to login -->
          <div class="back-to-login">
            <ion-button fill="clear" size="small" @click="goToLogin">
              <ion-icon :icon="icons.arrowBack" slot="start"></ion-icon>
              Volver al inicio de sesión
            </ion-button>
          </div>
        </div>
      </ion-card-content>
    </ion-card>
</template>

<script setup>
import { ref, watch, computed, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { useOtpStore } from '@/stores/otpStore.js'
import API from '@/utils/api/api.js'
import { paths } from '@/plugins/router/paths.js'
import { registerPush } from '@composables/usePushNotifications.js'

const router = useRouter()
const authStore = useAuthStore()
const otpStore = useOtpStore()

// Iconos desde el plugin
const icons = inject('icons', {})

// OTP_LENGTH: cantidad de dígitos del código
const OTP_LENGTH = 6

// Estado reactivo
const code = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const loadingText = ref('Verificando código...')
const resendCooldown = ref(0)
let resendTimer = null

// Identificador (email o username) del login pendiente
const identifier = computed(() => otpStore.identifier)

// Reinicia el contador de reenvío
const startResendCooldown = (seconds) => {
  stopResendCooldown()
  resendCooldown.value = seconds
  resendTimer = setInterval(() => {
    resendCooldown.value -= 1
    if (resendCooldown.value <= 0) {
      stopResendCooldown()
    }
  }, 1000)
}

const stopResendCooldown = () => {
  if (resendTimer) {
    clearInterval(resendTimer)
    resendTimer = null
  }
}

// Limpia mensajes
const clearMessages = () => {
  error.value = null
  success.value = null
}

// Asegura que exista la cookie CSRF antes de un POST
const ensureCsrf = async () => {
  if (API.getCookieValue('csrftoken')) return
  await API.get(API.CSRF_TOKEN)
}

// Redirige según el estado del usuario (misma lógica que el login)
const navigateAfterLogin = () => {
  if (authStore.needsTenantSetup) {
    router.replace('/tenant-setup')
  } else if (authStore.isSuperUser || authStore.isGlobalUser) {
    router.replace('/tenants')
  } else {
    router.replace('/home')
  }
}

// Verifica el código OTP
const verify = async () => {
  if (code.value.length < OTP_LENGTH) {
    error.value = 'Ingresa el código de 6 dígitos'
    return
  }

  loading.value = true
  clearMessages()

  try {
    await ensureCsrf()

    const response = await API.post(API.OTP_VERIFY, {
      username: identifier.value,
      code: code.value
    })

    const data = Array.isArray(response) ? response[0] : response

    if (!data?.access) {
      throw new Error('El backend no devolvió un access token')
    }

    const loginSuccess = authStore.login(data.access, data.refresh || null)
    if (!loginSuccess) {
      throw new Error('No se pudo procesar la autenticación')
    }

    success.value = '¡Código verificado! Iniciando sesión...'

    // Limpiar credenciales pendientes
    otpStore.clearPendingLogin()

    // Cargar perfil en segundo plano
    authStore.fetchUserProfile().catch(err => {
      console.warn('⚠️ Could not fetch user profile:', err)
    })

    // Registrar push en segundo plano
    registerPush().catch(e => console.warn('Push registration failed:', e))

    setTimeout(navigateAfterLogin, 300)
  } catch (err) {
    console.error('❌ Error verificando OTP:', err)
    const msg = err?.message || ''
    const isRejectedCode = msg.includes('Unauthorized') || msg.includes('Bad Request') ||
      msg.includes('invalid') || msg.includes('expirado')
    error.value = isRejectedCode
      ? '❌ Código inválido o expirado. Inténtalo de nuevo.'
      : `❌ ${msg}`
    code.value = ''
  } finally {
    loading.value = false
  }
}

// Reenvía el código usando las credenciales guardadas en memoria
const resend = async () => {
  if (!otpStore.password) {
    error.value = 'No se puede reenviar el código. Inicia sesión nuevamente.'
    return
  }

  loading.value = true
  loadingText.value = 'Reenviando código...'
  clearMessages()

  try {
    await ensureCsrf()

    await API.post(API.TOKEN, {
      username: otpStore.identifier,
      password: otpStore.password
    })

    success.value = '¡Código reenviado! Revisa tu correo.'
    code.value = ''
    startResendCooldown(30)
  } catch (err) {
    console.error('❌ Error reenviando OTP:', err)
    error.value = '❌ No se pudo reenviar el código. Inténtalo de nuevo.'
  } finally {
    loadingText.value = 'Verificando código...'
    loading.value = false
  }
}

// Auto-enviar cuando se completan los 6 dígitos
watch(code, (value) => {
  if (value.length === OTP_LENGTH && !loading.value && !error.value) {
    verify()
  }
})

// Lee el valor del ion-input-otp
const onCodeInput = (e) => {
  const val = e?.detail?.value ?? e?.target?.value ?? ''
  code.value = String(val)
  if (error.value) clearMessages()
}

const onCodeBlur = () => {
  if (code.value.length > 0 && code.value.length < OTP_LENGTH) {
    error.value = 'El código debe tener 6 dígitos'
  }
}

// Vuelve al login y limpia el flujo OTP
const goToLogin = () => {
  stopResendCooldown()
  otpStore.clearPendingLogin()
  router.replace(paths.LOGIN)
}

onMounted(() => {
  // Si no hay login pendiente, regresar al login
  if (!otpStore.identifier) {
    router.replace(paths.LOGIN)
    return
  }
  clearMessages()
})

onBeforeUnmount(() => {
  stopResendCooldown()
})
</script>

<style scoped>
.form-card {
  max-width: 480px;
  width: 100%;
  margin: 0;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.otp-item {
  --background: transparent;
  --padding-start: 0;
  --padding-end: 0;
  margin-bottom: 0.5rem;
}

.otp-input {
  width: 100%;
  --border-radius: 8px;
}

.otp-hint {
  font-size: 0.85rem;
  color: var(--color-zinc-500, #71717a);
  text-align: center;
  margin: 0.25rem 0 1rem;
}

.error-item {
  --background: transparent;
  margin-top: 0.5rem;
}

.success-item {
  --background: transparent;
  margin-top: 0.5rem;
}

.button-container {
  margin-top: 1rem;
}

.resend-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.resend-text {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-zinc-500, #71717a);
}

.back-to-login {
  display: flex;
  justify-content: center;
  margin-top: 0.25rem;
}
</style>
