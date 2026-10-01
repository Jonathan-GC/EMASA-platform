<template>
    <ion-card class="form-card">
      <ion-card-header class="text-center">
        <ion-card-title>¡Verifica tu identidad!</ion-card-title>
        <ion-card-subtitle v-if="method === 'email'">
          Enviamos un código de verificación a
          <strong>{{ email || identifier }}</strong>
        </ion-card-subtitle>
        <ion-card-subtitle v-else-if="method === 'totp'">
          Ingresa el código de 6 dígitos de tu aplicación de autenticación
        </ion-card-subtitle>
        <ion-card-subtitle v-else>
          Ingresa uno de tus códigos de recuperación
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content>
        <!-- Selector de método (solo si hay más de una opción) -->
        <div v-if="methodOptions.length > 1" class="method-switcher">
          <button
            v-for="opt in methodOptions"
            :key="opt.value"
            type="button"
            class="method-btn"
            :class="{ active: method === opt.value }"
            @click="selectMethod(opt.value)"
          >
            <ion-icon :icon="opt.icon"></ion-icon>
            <span>{{ opt.label }}</span>
          </button>
        </div>

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
              :length="codeLength"
              :inputmode="codeInputMode"
              :type="method === 'backup_code' ? 'text' : 'number'"
              :disabled="busy"
              :class="{ 'ion-invalid': !!error, 'ion-touched': !!error }"
              class="otp-input"
              @ionInput="onCodeInput"
              @ionBlur="onCodeBlur"
            ></ion-input-otp>
          </ion-item>

          <p class="otp-hint">
            {{ methodHint }}
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
              :disabled="busy || !isCodeComplete"
              @click="requestVerification"
            >
              <ion-icon :icon="icons.key" slot="start"></ion-icon>
              Verificar Código
            </ion-button>
          </div>

          <!-- Resend / switch to email -->
          <div class="resend-container">
            <p class="resend-text">{{ resendLabel }}</p>
            <ion-button
              fill="clear"
              size="small"
              :disabled="resendCooldown > 0 || busy"
              @click="resend"
            >
              <ion-icon :icon="icons.refresh" slot="start"></ion-icon>
              {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : resendActionLabel }}
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
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { useOtpStore } from '@/stores/otpStore.js'
import API from '@/utils/api/api.js'
import { paths } from '@/plugins/router/paths.js'
import { registerPush } from '@composables/usePushNotifications.js'
import { getTrustDevicePreference } from '@/utils/auth/deviceTrust.js'

const router = useRouter()
const authStore = useAuthStore()
const otpStore = useOtpStore()

// Iconos desde el plugin
const icons = inject('icons', {})

// Longitud del código según el método (los backup codes son de 8 caracteres)
const METHOD_LENGTHS = {
  totp: 6,
  email: 6,
  backup_code: 8
}

// Opciones del selector, filtradas por available_methods del backend
const buildMethodOptions = (methods) => {
  const catalog = {
    totp: { value: 'totp', label: 'Authenticator', icon: icons.phone_portrait },
    email: { value: 'email', label: 'Correo', icon: icons.mail },
    backup_code: { value: 'backup_code', label: 'Recuperación', icon: icons.key }
  }
  return methods.map(m => catalog[m]).filter(Boolean)
}

// Estado reactivo
const method = ref('email')
const code = ref('')
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const loadingText = ref('Verificando código...')
const resendCooldown = ref(0)
let resendTimer = null

// Contexto 2FA entregado por POST /token/
const identifier = computed(() => otpStore.identifier)
const email = computed(() => otpStore.email)
const availableMethods = computed(() => otpStore.availableMethods)
const allowDeviceTrust = computed(() => otpStore.allowDeviceTrust)

const methodOptions = computed(() => buildMethodOptions(availableMethods.value))

const codeLength = computed(() => METHOD_LENGTHS[method.value] || 6)
const codeInputMode = computed(() => (method.value === 'backup_code' ? 'text' : 'numeric'))
const isCodeComplete = computed(() => code.value.length === codeLength.value)

// Preferencia recordada de confianza ('always' | 'never' | null).
// Se lee una vez al montar porque localStorage no es reactivo.
const trustPreference = ref(getTrustDevicePreference())

// Decide si, tras un código válido, hay que mostrar la pantalla /trust.
// Se omite cuando el tenant no lo permite, cuando el usuario ya respondió con
// "no volver a preguntar", o cuando se usó un código de recuperación (para ese
// login no tiene sentido confiar en el dispositivo).
const trustScreenRequired = computed(() => {
  if (!allowDeviceTrust.value) return false
  if (trustPreference.value !== null) return false
  if (method.value === 'backup_code') return false
  return true
})

// Ventana de ~600 ms entre el "código verificado" y la navegación. `loading` vuelve
// a false en el finally antes de que salte el temporizador, así que sin este candado
// el formulario quedaría interactivo y un segundo toque reenviaría el mismo código.
const finishing = ref(false)

// Cualquier interacción del formulario durante una verificación o durante la
// transición a /trust (o al destino final) se ignora.
const busy = computed(() => loading.value || finishing.value)

const methodHint = computed(() => {
  if (method.value === 'totp') {
    return 'Abre Google Authenticator o tu app de códigos y escribe el código que muestre.'
  }
  if (method.value === 'backup_code') {
    return 'Escribe uno de los códigos de recuperación que guardaste al activar el authenticator.'
  }
  return 'Ingresa el código de 6 dígitos que enviamos a tu correo.'
})

const resendLabel = computed(() =>
  method.value === 'email'
    ? '¿No recibiste el código?'
    : '¿Prefieres recibirlo por correo?'
)

const resendActionLabel = computed(() =>
  method.value === 'email' ? 'Reenviar código' : 'Enviar código a mi correo'
)

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
  // Se limpia al navegar para que el estado de éxito conserve el contexto 2FA completo
  otpStore.clearPendingLogin()
  if (authStore.needsTenantSetup) {
    router.replace(paths.TENANT_SETUP)
  } else if (authStore.isSuperUser || authStore.isGlobalUser) {
    router.replace(paths.TENANTS)
  } else {
    router.replace(paths.HOME)
  }
}

// Cambia el método de verificación y reinicia el formulario
const selectMethod = (value) => {
  if (busy.value) return
  if (method.value === value) return
  method.value = value
  code.value = ''
  clearMessages()
  stopResendCooldown()
  resendCooldown.value = 0
}

// Verifica el código. La pregunta por confiar en el dispositivo NO se hace aquí:
// se hace después, en la pantalla /trust, y solo si el código es válido.
const requestVerification = () => {
  if (busy.value) return

  if (!isCodeComplete.value) {
    error.value = method.value === 'backup_code'
      ? 'Ingresa el código de recuperación completo'
      : 'Ingresa el código de 6 dígitos'
    return
  }

  verify()
}

// Verifica el código contra POST /users/auth/otp/verify/
const verify = async () => {
  if (busy.value) return
  loading.value = true
  clearMessages()

  try {
    await ensureCsrf()

    // trust_device siempre va en false: la confianza se decide DESPUÉS de
    // validar el código, en la pantalla /trust, vía POST
    // /users/sessions/trust_current/. Así un código inválido solo produce su
    // error y nunca alcanza a preguntar por confiar en el dispositivo.
    const response = await API.post(API.OTP_VERIFY, {
      username: identifier.value,
      code: code.value,
      method: method.value,
      trust_device: false
    })

    const data = Array.isArray(response) ? response[0] : response

    if (!data?.access) {
      throw new Error('El backend no devolvió un access token')
    }

    const loginSuccess = authStore.login(data.access, data.refresh || null)
    if (!loginSuccess) {
      throw new Error('No se pudo procesar la autenticación')
    }

    // Si el usuario ya había pedido confiar siempre en este dispositivo, no se vuelve
// a preguntar: se concede la confianza directamente. Hace falta porque el verify
// siempre va con trust_device=false, así que el backend no emite la cookie por sí
// solo. Un fallo aquí no debe impedir el ingreso, solo se avisa por consola.
if (allowDeviceTrust.value && trustPreference.value === 'always') {
      try {
        await API.post(API.SESSIONS_TRUST_CURRENT, { trust: true })
      } catch (e) {
        console.warn('⚠️ No se pudo marcar el dispositivo como de confianza:', e)
      }
    }

    success.value = '¡Código verificado! Iniciando sesión...'

    // Cargar perfil en segundo plano
    authStore.fetchUserProfile().catch(err => {
      console.warn('⚠️ Could not fetch user profile:', err)
    })

    // Registrar push en segundo plano
    registerPush().catch(e => console.warn('Push registration failed:', e))

    // La decisión de confianza va en una pantalla aparte, no en un modal: así el
    // usuario no puede descartarla por error ni perder el contexto del OTP.
    const decisionNeeded = trustScreenRequired.value
    finishing.value = true
    if (decisionNeeded) {
      otpStore.requireTrustDecision()
      setTimeout(() => router.replace(paths.TRUST), 600)
      return
    }

    setTimeout(navigateAfterLogin, 600)
  } catch (err) {
    console.error('❌ Error verificando OTP:', err)
    const msg = err?.message || ''
    const isRejectedCode = msg.includes('Unauthorized') || msg.includes('Bad Request') ||
      msg.includes('invalid') || msg.includes('expirado') || msg.includes('attempt')
    error.value = isRejectedCode
      ? '❌ Código inválido o expirado. Inténtalo de nuevo.'
      : `❌ ${msg}`
    code.value = ''
  } finally {
    loading.value = false
  }
}

// Envía (o reenvía) el código por correo.
// OJO: no se usa POST /token/ porque el backend solo despacha el email OTP
// cuando primary_method === 'email'; con TOTP activo el correo no se envía.
const resend = async () => {
  if (busy.value) return

  if (!otpStore.identifier) {
    error.value = 'No se puede reenviar el código. Inicia sesión nuevamente.'
    return
  }

  loading.value = true
  loadingText.value = 'Enviando código...'
  clearMessages()

  try {
    await ensureCsrf()

    await API.post(API.OTP_REQUEST, {
      username: otpStore.identifier
    })

    // El endpoint siempre despacha por correo, así que el método pasa a email
    method.value = 'email'
    success.value = '¡Código enviado! Revisa tu correo.'
    code.value = ''
    startResendCooldown(30)
  } catch (err) {
    console.error('❌ Error reenviando OTP:', err)
    error.value = '❌ No se pudo enviar el código. Inténtalo de nuevo.'
  } finally {
    loadingText.value = 'Verificando código...'
    loading.value = false
  }
}

// Auto-enviar cuando el código queda completo
watch(code, (value) => {
  if (value.length === codeLength.value && !loading.value && !error.value) {
    requestVerification()
  }
})

// Cambia el método seleccionado al rotar el código OTP
watch(codeLength, () => {
  if (code.value.length > codeLength.value) {
    code.value = code.value.slice(0, codeLength.value)
  }
})

// Lee el valor del ion-input-otp
const onCodeInput = (e) => {
  const raw = e?.detail?.value ?? e?.target?.value ?? ''
  // Normaliza: los backup codes se emiten en mayúsculas
  const val = method.value === 'backup_code' ? String(raw).toUpperCase() : String(raw)
  code.value = val.slice(0, codeLength.value)
  if (error.value) clearMessages()
}

const onCodeBlur = () => {
  if (code.value.length > 0 && code.value.length < codeLength.value) {
    error.value = method.value === 'backup_code'
      ? `El código debe tener ${codeLength.value} caracteres`
      : 'El código debe tener 6 dígitos'
  }
}

// Vuelve al login y limpia el flujo OTP
const goToLogin = () => {
  if (finishing.value) return
  stopResendCooldown()
  otpStore.clearPendingLogin()
  router.replace(paths.LOGIN)
}

onMounted(() => {
  // Si no hay login pendiente, recuperar el contexto 2FA de sessionStorage
  // (la WebView móvil puede haber recreado el store Pinia)
  if (!otpStore.identifier) {
    const restored = otpStore.restoreContext()
    if (!restored || !otpStore.identifier) {
      router.replace(paths.LOGIN)
      return
    }
  }

  // El backend indica el método preferido
  method.value = availableMethods.value.includes(otpStore.primaryMethod)
    ? otpStore.primaryMethod
    : (availableMethods.value[0] || 'email')

  clearMessages()
})

onBeforeUnmount(() => {
  stopResendCooldown()
})
</script>

<style scoped>
.form-card {
  max-width: 560px;
  width: 100%;
  margin: 0;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.otp-item {
  --background: transparent;
  --padding-start: 0;
  --padding-end: 0;
  --inner-padding-start: 0;
  --inner-padding-end: 0;
  margin-bottom: 0.5rem;
}

/* Selector de método de verificación */
.method-switcher {
  display: flex;
  gap: 0.375rem;
  padding: 0.25rem;
  margin-bottom: 1rem;
  border-radius: 12px;
  background: rgba(113, 113, 122, 0.08);
}

.method-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 0.25rem;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--color-zinc-600, #52525b);
  font-size: 0.7rem;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.method-btn ion-icon {
  font-size: 1.25rem;
}

.method-btn.active {
  background: var(--ion-background-color, #fff);
  color: var(--ion-color-primary, #2563eb);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  font-weight: 600;
}

.otp-input {
  width: 100%;
  --border-radius: 8px;
  --width: clamp(16px, calc((100vw - 188px) / 8), 48px);
  --min-width: clamp(16px, calc((100vw - 188px) / 8), 40px);
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
