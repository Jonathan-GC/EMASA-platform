<template>
  <div class="content-card">
    <div class="card-header-row">
      <h3 class="content-card-title">
        <ion-icon :icon="icons.server"></ion-icon>
        Dispositivos activos
      </h3>
      <div class="header-actions">
        <ion-button
          v-if="hasTrustedDevices"
          fill="outline"
          size="small"
          color="danger"
          class="header-btn"
          :disabled="loading"
          @click="confirmRevokeTrustAll"
        >
          <ion-icon :icon="icons.shield" slot="start"></ion-icon>
          Quitar confianza de todas
        </ion-button>
        <ion-button
          v-if="hasOtherDevices"
          fill="outline"
          size="small"
          color="danger"
          class="header-btn"
          :disabled="loading"
          @click="confirmRevokeOthers"
        >
          <ion-icon :icon="icons.logOut" slot="start"></ion-icon>
          Cerrar otras
        </ion-button>
      </div>
    </div>

    <p class="card-desc">
      Dispositivos con una sesión iniciada en tu cuenta; varios navegadores o
      pestañas del mismo equipo se agrupan en un solo dispositivo. Los marcados
      como de confianza omiten el código de verificación al entrar. Si ves uno
      que no reconoces, quítale la confianza y cambia tu contraseña.
    </p>

    <div v-if="loading" class="loading-state">
      <ion-spinner name="crescent"></ion-spinner>
    </div>

    <p v-else-if="devices.length === 0" class="empty-state">
      No hay dispositivos activos registrados.
    </p>

    <div v-else class="device-list">
      <div
        v-for="device in devices"
        :key="device.id"
        class="device-item"
        :class="{ current: device.is_current }"
      >
        <div class="device-info">
          <DeviceIcon
            :current="device.is_current"
            :device-name="device.device_name"
          />
          <div class="device-text">
            <span class="device-name">
              {{ device.device_name || 'Dispositivo desconocido' }}
              <ion-chip v-if="device.is_current" color="primary" size="small">Este dispositivo</ion-chip>
              <ion-chip v-if="device.is_trusted" color="success" size="small">
                <ion-icon :icon="icons.shield"></ion-icon>
                De confianza
              </ion-chip>
              <ion-chip v-if="device.sessions_count > 1" color="medium" size="small">
                {{ device.sessions_count }} sesiones
              </ion-chip>
            </span>
            <span class="device-meta">
              <ion-icon :icon="icons.globe"></ion-icon>
              {{ device.ip_address || 'IP desconocida' }}
            </span>
            <span class="device-meta">
              <ion-icon :icon="icons.info"></ion-icon>
              Última actividad: {{ formatDate(device.last_activity) }}
            </span>
          </div>
        </div>

        <!-- Otro dispositivo con confianza: revocar la confianza termina
             todas sus sesiones, así que es la acción completa. -->
        <ion-button
          v-if="!device.is_current && device.is_trusted"
          fill="clear"
          size="small"
          color="danger"
          class="device-btn"
          :disabled="loading || revokingId === device.id"
          @click="confirmRevokeTrust(device)"
        >
          <ion-spinner v-if="revokingId === device.id" name="dots" slot="start"></ion-spinner>
          <ion-icon v-else :icon="icons.shield" slot="start"></ion-icon>
          Quitar confianza
        </ion-button>

        <!-- Otro dispositivo sin confianza: cerrar una de sus sesiones. -->
        <ion-button
          v-else-if="!device.is_current"
          fill="clear"
          size="small"
          color="danger"
          class="device-btn"
          :disabled="loading || revokingId === device.id"
          @click="confirmRevoke(device)"
        >
          <ion-spinner v-if="revokingId === device.id" name="dots" slot="start"></ion-spinner>
          Cerrar
        </ion-button>

        <!-- Este dispositivo cuando es de confianza: quitar la confianza
             cierra la sesión actual (logout intencional). -->
        <ion-button
          v-else-if="device.is_trusted"
          fill="clear"
          size="small"
          color="danger"
          class="device-btn"
          :disabled="loading || revokingId === device.id"
          @click="confirmRevokeTrust(device)"
        >
          <ion-spinner v-if="revokingId === device.id" name="dots" slot="start"></ion-spinner>
          <ion-icon v-else :icon="icons.shield" slot="start"></ion-icon>
          Quitar confianza
        </ion-button>
      </div>
    </div>

    <ion-modal :is-open="isConfirmOpen" @did-dismiss="closeConfirm" class="confirm-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>{{ confirmTitle }}</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeConfirm">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <div class="confirm-content">
        <div class="confirm-icon">
          <ion-icon :icon="confirmIcon || icons.logOut" size="large"></ion-icon>
        </div>
        <p class="confirm-text">{{ confirmMessage }}</p>
        <div class="modal-actions">
          <ion-button fill="outline" @click="closeConfirm">Cancelar</ion-button>
          <ion-button color="danger" :disabled="loading" @click="executeAction">
            <ion-spinner v-if="loading" name="crescent" slot="start"></ion-spinner>
            {{ confirmActionLabel }}
          </ion-button>
        </div>
      </div>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { toastController } from '@ionic/vue'
import { useRouter } from 'vue-router'
import API from '@/utils/api/api'
import { paths } from '@/plugins/router/paths.js'
import { useAuthStore } from '@/stores/authStore.js'
import { resetTrustDevicePreference } from '@/utils/auth/deviceTrust.js'

const icons = inject('icons', {})
const router = useRouter()
const authStore = useAuthStore()

// GET /users/sessions/devices/: sesiones activas agregadas por dispositivo.
// Cada dispositivo trae { id (sesión representativa), device_name,
// ip_address, last_activity, is_trusted, is_current, sessions_count }.
const devices = ref([])
const loading = ref(false)
const revokingId = ref(null)

const isConfirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmActionLabel = ref('Cerrar sesión')
const confirmIcon = ref(null)
// Acción pendiente del modal:
//   { type: 'revoke' | 'revoke_trust' | 'revoke_others' | 'revoke_trust_all', id?: string }
const pendingAction = ref(null)

const hasOtherDevices = computed(() => devices.value.some(d => !d.is_current))
const hasTrustedDevices = computed(() => devices.value.some(d => d.is_trusted))

const formatDate = (value) => {
  if (!value) return 'desconocida'
  try {
    return new Date(value).toLocaleString()
  } catch (err) {
    return value
  }
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

const fetchDevices = async () => {
  loading.value = true
  try {
    const response = await API.get(API.SESSIONS_DEVICES)
    devices.value = Array.isArray(response) ? response : (response?.results || [])
  } catch (err) {
    console.error('Error al cargar los dispositivos:', err)
    devices.value = []
    await showToast('No se pudieron cargar los dispositivos activos.')
  } finally {
    loading.value = false
  }
}

const openConfirm = () => {
  isConfirmOpen.value = true
}

const confirmRevoke = (device) => {
  pendingAction.value = { type: 'revoke', id: device.id }
  confirmTitle.value = 'Cerrar sesión'
  confirmActionLabel.value = 'Cerrar sesión'
  confirmIcon.value = icons.logOut

  const count = device.sessions_count || 1
  if (count > 1) {
    confirmMessage.value =
      `"${device.device_name || 'este dispositivo'}" tiene ${count} sesiones abiertas. ` +
      'Esta acción cierra una de ellas; puedes repetirla para cerrar las demás.'
  } else {
    confirmMessage.value =
      `Se cerrará la sesión de "${device.device_name || 'este dispositivo'}" ` +
      `(${device.ip_address || 'IP desconocida'}). Necesitarás volver a iniciar sesión ahí.`
  }
  openConfirm()
}

const confirmRevokeTrust = (device) => {
  pendingAction.value = { type: 'revoke_trust', id: device.id }
  confirmTitle.value = 'Quitar confianza'
  confirmActionLabel.value = 'Quitar confianza'
  confirmIcon.value = icons.shield

  const count = device.sessions_count || 1
  if (device.is_current) {
    confirmMessage.value =
      'Este dispositivo dejará de ser de confianza y se cerrarán sus sesiones, incluida la actual. ' +
      'La próxima vez tendrás que iniciar sesión y verificar con un código.'
  } else if (count > 1) {
    confirmMessage.value =
      `Se quitará la confianza de "${device.device_name || 'este dispositivo'}" ` +
      `(${device.ip_address || 'IP desconocida'}) y se cerrarán sus ${count} sesiones. ` +
      'Ese dispositivo tendrá que volver a iniciar sesión y verificar con un código.'
  } else {
    confirmMessage.value =
      `Se quitará la confianza de "${device.device_name || 'este dispositivo'}" ` +
      `(${device.ip_address || 'IP desconocida'}) y se cerrará su sesión. ` +
      'Ese dispositivo tendrá que volver a iniciar sesión y verificar con un código.'
  }
  openConfirm()
}

const confirmRevokeOthers = () => {
  pendingAction.value = { type: 'revoke_others' }
  confirmTitle.value = 'Cerrar otras sesiones'
  confirmMessage.value =
    'Se cerrarán todas las sesiones abiertas en otros dispositivos. ' +
    'Solo se mantendrán las de este dispositivo.'
  confirmActionLabel.value = 'Cerrar otras'
  confirmIcon.value = icons.logOut
  openConfirm()
}

const confirmRevokeTrustAll = () => {
  pendingAction.value = { type: 'revoke_trust_all' }
  const trusted = devices.value.filter(d => d.is_trusted)
  const count = trusted.length
  const currentTrusted = trusted.some(d => d.is_current)

  confirmTitle.value = 'Quitar confianza de todas'
  confirmMessage.value =
    `Se quitará la confianza de ${count} ${count === 1 ? 'dispositivo de confianza' : 'dispositivos de confianza'} ` +
    'y se cerrarán todas sus sesiones; deberán iniciar sesión y verificar con un código. ' +
    (currentTrusted
      ? 'Incluye este dispositivo: tu sesión se cerrará ahora.'
      : 'Este dispositivo no es de confianza, así que tu sesión continuará abierta.')
  confirmActionLabel.value = 'Quitar confianza'
  confirmIcon.value = icons.shield
  openConfirm()
}

const closeConfirm = () => {
  isConfirmOpen.value = false
  pendingAction.value = null
}

// Quitar la confianza del dispositivo actual equivale a cerrar la sesión
// propia: el backend borra las cookies device_trust_token y refresh_token,
// así que hay que hacer logout intencional. También se restablece la
// preferencia local "no volver a preguntar"; si se dejara en 'always', el
// próximo ingreso volvería a confiar automáticamente en este dispositivo.
const logoutCurrentDevice = async (message) => {
  resetTrustDevicePreference()
  await showToast(message, 'success')
  authStore.logout()
  router.replace(paths.LOGIN)
}

const executeAction = async () => {
  const action = pendingAction.value
  if (!action) return

  loading.value = true
  if (action.id) revokingId.value = action.id

  try {
    if (action.type === 'revoke') {
      await API.post(API.SESSIONS_REVOKE(action.id), {})
      closeConfirm()
      await fetchDevices()
      await showToast('Sesión cerrada.', 'success')
    } else if (action.type === 'revoke_others') {
      await API.post(API.SESSIONS_REVOKE_OTHERS, {})
      closeConfirm()
      await fetchDevices()
      await showToast('Las sesiones de otros dispositivos fueron cerradas.', 'success')
    } else if (action.type === 'revoke_trust') {
      // El flag is_current es del grupo: aunque la sesión representativa no
      // sea la actual, revocar la confianza de este dispositivo también
      // termina la sesión propia (el backend revoca las sesiones hermanas
      // que comparten el trust_hash).
      const target = devices.value.find(d => d.id === action.id)
      await API.post(API.SESSIONS_REVOKE_TRUST(action.id), {})
      closeConfirm()
      if (target?.is_current) {
        await logoutCurrentDevice('Confianza revocada. Tu sesión se cerró en este dispositivo.')
        return
      }
      await fetchDevices()
      await showToast('Confianza y sesiones revocadas en ese dispositivo.', 'success')
    } else if (action.type === 'revoke_trust_all') {
      // Se consulta antes del POST: después de revocar, la lista ya no
      // tendría el dispositivo actual marcado como de confianza.
      const currentWasTrusted = devices.value.some(d => d.is_current && d.is_trusted)
      const response = await API.post(API.SESSIONS_REVOKE_TRUST_ALL, {})
      closeConfirm()

      if (currentWasTrusted) {
        await logoutCurrentDevice('Confianza revocada. Tu sesión se cerró en este dispositivo.')
        return
      }

      await fetchDevices()
      const count = response?.revoked_count
      await showToast(
        count
          ? `Se quitó la confianza de todos los dispositivos y se cerraron ${count} ${count === 1 ? 'sesión' : 'sesiones'}.`
          : 'No había dispositivos de confianza.',
        'success'
      )
    }
  } catch (err) {
    console.error('Error al aplicar la acción sobre dispositivos:', err)
    closeConfirm()
    await showToast('No se pudo completar la acción. Inténtalo de nuevo.')
  } finally {
    loading.value = false
    revokingId.value = null
  }
}

onMounted(fetchDevices)
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

.card-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.content-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--ion-text-color);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.header-btn {
  --border-radius: 8px;
  text-transform: none;
  font-weight: 500;
}

.card-desc {
  margin: 8px 0 20px 0;
  font-size: 0.85rem;
  line-height: 1.5;
  color: var(--ion-color-medium);
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.empty-state {
  margin: 0;
  padding: 24px 0;
  text-align: center;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
}

.device-item.current {
  border-color: var(--ion-color-primary);
  background: rgba(37, 99, 235, 0.04);
}

.device-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.device-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ion-text-color);
}

.device-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--ion-color-medium);
}

.device-meta ion-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}

.device-btn {
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
  gap: 16px;
  padding: 24px 32px 28px;
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
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--ion-color-medium);
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

  .device-item {
    flex-direction: column;
    align-items: stretch;
  }

  .device-btn {
    align-self: flex-end;
  }
}
</style>
