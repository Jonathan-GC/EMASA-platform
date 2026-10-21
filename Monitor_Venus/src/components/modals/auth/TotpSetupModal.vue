<template>
  <ion-modal :is-open="isOpen" @did-dismiss="close">
    <ion-header class="custom">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-button @click="close">
            <ion-icon :icon="icons.chevronBack" slot="icon-only"></ion-icon>
          </ion-button>
        </ion-buttons>
        <ion-title>Activar Authenticator</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content>
      <div class="setup-content">
        <!-- Paso 1: cargar -->
        <div v-if="loadingSetup" class="step-state">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Generando clave de seguridad...</p>
        </div>

        <template v-else-if="secret">
          <p class="step-hint">
            Paso 1 de 2 · Escanea el código con Google Authenticator, Authy o
            cualquier app compatible con TOTP.
          </p>

          <div class="qr-wrapper">
            <qrcode-vue
              v-if="otpauthUri"
              :value="otpauthUri"
              :size="200"
              level="M"
              render-as="canvas"
            />
          </div>

          <!-- Ingreso manual por si la cámara no está disponible -->
          <div class="manual-secret">
            <p class="manual-label">¿No puedes escanear? Ingresa esta clave manualmente:</p>
            <div class="secret-row">
              <code class="secret-value">{{ secret }}</code>
              <ion-button
                fill="clear"
                size="small"
                class="copy-btn"
                @click="copySecret"
              >
                <ion-icon :icon="icons.copy" slot="icon-only"></ion-icon>
              </ion-button>
            </div>
          </div>

          <p class="step-hint">
            Paso 2 de 2 · Ingresa el código de 6 dígitos que muestra tu aplicación.
          </p>

          <div class="code-input-wrap">
            <ion-input-otp
              :value="code"
              length="6"
              inputmode="numeric"
              type="number"
              :disabled="loading || !secret"
              class="otp-input"
              @ionInput="onCodeInput"
            ></ion-input-otp>
          </div>

          <ion-item v-if="error" lines="none" class="error-item">
            <ion-label color="danger">
              <ion-icon :icon="icons.alertCircle"></ion-icon>
              {{ error }}
            </ion-label>
          </ion-item>

          <ion-button
            expand="block"
            class="action-btn"
            :disabled="loading || code.length !== 6"
            @click="activate"
          >
            <ion-icon :icon="icons.checkmark" slot="start"></ion-icon>
            Activar Authenticator
          </ion-button>
        </template>

        <div v-else class="step-state">
          <ion-icon :icon="icons.error" class="error-big"></ion-icon>
          <p>{{ error || 'No se pudo iniciar la configuración.' }}</p>
          <ion-button fill="outline" class="action-btn" @click="requestSetup">
            Reintentar
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-modal>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonIcon,
  IonContent,
  IonItem,
  IonLabel,
  IonSpinner,
  IonInputOtp
} from '@ionic/vue'
import QrcodeVue from 'qrcode.vue'
import API from '@/utils/api/api.js'

// Iconos desde el plugin
const icons = inject('icons', {})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

// Emite los backup codes para que el padre muestre el modal irrecuperable
const emit = defineEmits(['activated', 'closed'])

const secret = ref('')
const otpauthUri = ref('')
const code = ref('')
const loading = ref(false)
const loadingSetup = ref(false)
const error = ref(null)

const reset = () => {
  secret.value = ''
  otpauthUri.value = ''
  code.value = ''
  loading.value = false
  loadingSetup.value = false
  error.value = null
}

const ensureCsrf = async () => {
  if (API.getCookieValue('csrftoken')) return
  await API.get(API.CSRF_TOKEN)
}

const requestSetup = async () => {
  loadingSetup.value = true
  error.value = null
  code.value = ''

  try {
    await ensureCsrf()
    const response = await API.post(API.MFA_TOTP_SETUP, {})
    const data = Array.isArray(response) ? response[0] : response

    if (!data?.secret) {
      throw new Error('El backend no devolvió una clave de autenticación')
    }

    secret.value = data.secret
    otpauthUri.value = data.otpauth_uri || ''
  } catch (err) {
    console.error('❌ Error iniciando setup TOTP:', err)
    error.value = err?.message || 'No se pudo generar la clave de seguridad.'
  } finally {
    loadingSetup.value = false
  }
}

const onCodeInput = (e) => {
  const val = e?.detail?.value ?? e?.target?.value ?? ''
  code.value = String(val).replace(/\D/g, '').slice(0, 6)
  if (error.value) error.value = null
}

const copySecret = async () => {
  try {
    await navigator.clipboard.writeText(secret.value)
  } catch (err) {
    console.warn('No se pudo copiar la clave:', err)
  }
}

const activate = async () => {
  loading.value = true
  error.value = null

  try {
    await ensureCsrf()
    const response = await API.post(API.MFA_TOTP_ACTIVATE, { code: code.value })
    const data = Array.isArray(response) ? response[0] : response

    const backupCodes = Array.isArray(data?.backup_codes) ? data.backup_codes : []
    if (backupCodes.length === 0) {
      throw new Error('El backend no devolvió los códigos de respaldo')
    }

    emit('activated', backupCodes)
    reset()
  } catch (err) {
    console.error('❌ Error activando TOTP:', err)
    error.value = err?.message?.includes('Invalid')
      ? 'El código es inválido o expiró. Genera uno nuevo e inténtalo de nuevo.'
      : (err?.message || 'No se pudo activar el authenticator.')
    code.value = ''
  } finally {
    loading.value = false
  }
}

const close = () => {
  reset()
  emit('closed')
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) requestSetup()
  }
)
</script>

<style scoped>
.setup-content {
  padding: 1.25rem 1.25rem 2rem;
  max-width: 420px;
  margin: 0 auto;
}

.step-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1rem;
  text-align: center;
  color: var(--color-zinc-600, #52525b);
}

.error-big {
  font-size: 48px;
  color: #ef4444;
}

.step-hint {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  line-height: 1.45;
  text-align: center;
  color: var(--color-zinc-500, #71717a);
}

.qr-wrapper {
  display: flex;
  justify-content: center;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 14px;
  background: #fff;
  border: 1px solid rgba(113, 113, 122, 0.2);
}

.manual-secret {
  margin-bottom: 1.25rem;
}

.manual-label {
  margin: 0 0 0.4rem;
  font-size: 0.8rem;
  color: var(--color-zinc-500, #71717a);
  text-align: center;
}

.secret-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.secret-value {
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  background: rgba(113, 113, 122, 0.1);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.85rem;
  letter-spacing: 0.06em;
  word-break: break-all;
  text-align: center;
}

.copy-btn {
  --color: var(--ion-color-primary, #2563eb);
  flex-shrink: 0;
}

.code-input-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.otp-input {
  width: 100%;
  max-width: 320px;
  --border-radius: 8px;
}

.error-item {
  --background: transparent;
  margin-bottom: 0.5rem;
}

.action-btn {
  --border-radius: 10px;
  min-height: 46px;
  text-transform: none;
  font-weight: 500;
}
</style>
