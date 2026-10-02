<template>
  <div class="content-card">
    <h3 class="content-card-title">
      <ion-icon :icon="icons.shield"></ion-icon>
      Seguridad de la cuenta
    </h3>

    <div v-if="loadingStatus" class="loading-state">
      <ion-spinner name="crescent"></ion-spinner>
    </div>

    <template v-else>
      <div class="mfa-block">
        <div class="mfa-header">
          <div class="mfa-name">
            <ion-icon :icon="icons.phone_portrait" class="mfa-icon"></ion-icon>
            <div class="mfa-text">
              <span class="mfa-title">Verificación en dos pasos</span>
              <span class="mfa-desc">Códigos de 6 dígitos desde tu app de autenticación</span>
            </div>
          </div>
          <ion-chip :color="totpActive ? 'success' : 'medium'" size="small">
            {{ totpActive ? 'Activo' : 'Inactivo' }}
          </ion-chip>
        </div>

        <ion-item v-if="backupCodesRemaining > 0" lines="none" class="backup-remain">
          <ion-icon :icon="icons.key" slot="start" class="backup-icon"></ion-icon>
          <ion-label>
            <strong>{{ backupCodesRemaining }}</strong>
            {{ backupCodesRemaining === 1 ? 'código de recuperación disponible' : 'códigos de recuperación disponibles' }}
          </ion-label>
        </ion-item>

        <p v-if="totpActive" class="mfa-note">
          Si pierdes el acceso a tu aplicación, usa un código de recuperación para
          entrar y vuelve a activar el authenticator.
        </p>

        <div class="mfa-actions">
          <ion-button v-if="!totpActive" class="action-btn" :disabled="loadingAction" @click="openSetup">
            <ion-icon :icon="icons.add" slot="start"></ion-icon>
            Activar Authenticator
          </ion-button>
          <ion-button
            v-else
            fill="outline"
            color="danger"
            class="action-btn"
            :disabled="loadingAction"
            @click="openDeactivate"
          >
            <ion-icon :icon="icons.delete" slot="start"></ion-icon>
            Desactivar
          </ion-button>
        </div>
      </div>

      <div class="mfa-block">
        <div class="mfa-header">
          <div class="mfa-name">
            <ion-icon :icon="icons.mail" class="mfa-icon"></ion-icon>
            <div class="mfa-text">
              <span class="mfa-title">Código por correo</span>
              <span class="mfa-desc">Enviado a {{ userEmail || 'tu correo registrado' }}</span>
            </div>
          </div>
          <ion-chip :color="emailActive ? 'success' : 'medium'" size="small">
            {{ emailActive ? 'Disponible' : 'Sin correo' }}
          </ion-chip>
        </div>
      </div>
      <div class="mfa-block">
        <div class="mfa-header">
          <div class="mfa-name">
            <ion-icon :icon="icons.shield" class="mfa-icon"></ion-icon>
            <div class="mfa-text">
              <span class="mfa-title">Dispositivo de confianza</span>
              <span class="mfa-desc">{{ trustPreferenceText }}</span>
            </div>
          </div>
          <ion-button
            v-if="trustPreference"
            fill="clear"
            size="small"
            class="trust-reset-btn"
            @click="resetTrustPreference"
          >
            Cambiar
          </ion-button>
        </div>
      </div>
    </template>

    <totp-setup-modal
      :is-open="isSetupOpen"
      @activated="onActivated"
      @closed="isSetupOpen = false"
    />

    <backup-codes-modal
      :is-open="isBackupCodesOpen"
      :codes="backupCodes"
      @closed="closeBackupCodes"
    />

    <ion-modal :is-open="isDeactivateOpen" @did-dismiss="closeDeactivate" class="confirm-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Desactivar Authenticator</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeDeactivate">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <div class="confirm-content">
        <div class="confirm-icon">
          <ion-icon :icon="icons.warning" size="large"></ion-icon>
        </div>
        <p class="confirm-text">
          Se eliminarán tu aplicación de autenticación y todos tus códigos de
          recuperación. Confirma tu contraseña para continuar.
        </p>

        <ion-item lines="none" class="password-item">
          <ion-input
            v-model="password"
            type="password"
            label="Contraseña actual"
            label-placement="stacked"
            :disabled="loadingAction"
            @ionInput="onPasswordInput"
          ></ion-input>
        </ion-item>

        <p v-if="deactivateError" class="confirm-error">{{ deactivateError }}</p>

        <div class="modal-actions">
          <ion-button fill="outline" @click="closeDeactivate">Cancelar</ion-button>
          <ion-button
            color="danger"
            :disabled="loadingAction || !password"
            @click="confirmDeactivate"
          >
            <ion-spinner v-if="loadingAction" name="crescent" slot="start"></ion-spinner>
            Desactivar
          </ion-button>
        </div>
      </div>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { toastController } from '@ionic/vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'
import TotpSetupModal from '@/components/modals/auth/TotpSetupModal.vue'
import BackupCodesModal from '@/components/modals/auth/BackupCodesModal.vue'
import {
  getTrustDevicePreference,
  resetTrustDevicePreference
} from '@/utils/auth/deviceTrust'

const icons = inject('icons', {})
const authStore = useAuthStore()

const loadingStatus = ref(true)
const loadingAction = ref(false)

// GET /users/auth/mfa/status/ ->
// { totp_active, email_active, backup_codes_remaining, methods[] }
const totpActive = ref(false)
const emailActive = ref(false)
const backupCodesRemaining = ref(0)

const isSetupOpen = ref(false)
const isBackupCodesOpen = ref(false)
const isDeactivateOpen = ref(false)

const backupCodes = ref([])
const password = ref('')
const deactivateError = ref(null)

const userEmail = computed(() => authStore.email || '')

const trustPreference = ref(getTrustDevicePreference())

const trustPreferenceText = computed(() => {
  if (trustPreference.value === 'always') {
    return 'Este dispositivo se guardará como de confianza automáticamente en los próximos ingresos.'
  }
  if (trustPreference.value === 'never') {
    return 'Se te pedirá el código de verificación en cada inicio de sesión, aunque confíes en este dispositivo.'
  }
  return 'Se te preguntará en el próximo inicio de sesión si quieres recordarlo.'
})

const resetTrustPreference = () => {
  resetTrustDevicePreference()
  trustPreference.value = null
}

const showToast = async (message, color = 'danger') => {
  const toast = await toastController.create({
    message,
    duration: 4000,
    color,
    position: 'top'
  })
  await toast.present()
}

const fetchStatus = async () => {
  loadingStatus.value = true
  try {
    const response = await API.get(API.MFA_STATUS)
    const data = Array.isArray(response) ? response[0] : response

    totpActive.value = !!data?.totp_active
    emailActive.value = !!data?.email_active
    backupCodesRemaining.value = Number(data?.backup_codes_remaining) || 0
  } catch (err) {
    console.error('Error al cargar el estado de MFA:', err)
    await showToast('No se pudo cargar la configuración de seguridad.')
  } finally {
    loadingStatus.value = false
  }
}

const openSetup = () => {
  backupCodes.value = []
  isSetupOpen.value = true
}

const onActivated = (codes) => {
  isSetupOpen.value = false
  backupCodes.value = codes
  isBackupCodesOpen.value = true
  fetchStatus()
}

const closeBackupCodes = () => {
  isBackupCodesOpen.value = false
  backupCodes.value = []
}

const openDeactivate = () => {
  password.value = ''
  deactivateError.value = null
  isDeactivateOpen.value = true
}

const closeDeactivate = () => {
  isDeactivateOpen.value = false
  password.value = ''
  deactivateError.value = null
}

const onPasswordInput = (e) => {
  password.value = e?.detail?.value ?? e?.target?.value ?? ''
  if (deactivateError.value) deactivateError.value = null
}

const confirmDeactivate = async () => {
  loadingAction.value = true
  deactivateError.value = null

  try {
    await API.post(API.MFA_TOTP_DEACTIVATE, { password: password.value })
    closeDeactivate()
    await fetchStatus()
    await showToast('Authenticator desactivado.', 'success')
  } catch (err) {
    console.error('Error al desactivar TOTP:', err)
    const msg = err?.message || ''
    deactivateError.value = msg.includes('Invalid password')
      ? 'La contraseña es incorrecta.'
      : 'No se pudo desactivar el authenticator.'
  } finally {
    loadingAction.value = false
  }
}

onMounted(fetchStatus)
</script>

<style scoped>
.content-card {
  box-sizing: border-box;
  width: 100%;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.content-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--ion-text-color);
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.mfa-block {
  padding: 14px 16px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
  margin-bottom: 12px;
}

.mfa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.mfa-name {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.mfa-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
  color: var(--ion-color-primary);
}

.mfa-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.mfa-title {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ion-text-color);
}

.mfa-desc {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.backup-remain {
  --background: transparent;
  --padding-start: 0;
  font-size: 0.85rem;
  margin-top: 0.75rem;
}

.backup-icon {
  color: var(--ion-color-warning);
  margin-inline-end: 8px;
}

.mfa-note {
  margin: 0.75rem 0 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: var(--ion-color-medium);
}

.mfa-actions {
  margin-top: 0.75rem;
}

.action-btn {
  --border-radius: 10px;
  text-transform: none;
  font-weight: 500;
}

.trust-reset-btn {
  --border-radius: 8px;
  flex-shrink: 0;
  text-transform: none;
  font-weight: 500;
}

.confirm-modal {
  --width: 340px;
  --height: auto;
  --max-height: 90vh;
  --border-radius: 16px;
}

.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 24px 24px 20px;
  text-align: center;
}

.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.confirm-text {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--ion-color-medium);
}

.password-item {
  --background: transparent;
  width: 100%;
}

.confirm-error {
  margin: 0;
  font-size: 0.82rem;
  color: #c0392b;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .content-card {
    padding: 16px;
  }
}
</style>
