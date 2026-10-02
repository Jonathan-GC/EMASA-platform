<template>
  <div class="content-card">
    <div class="card-header-row">
      <h3 class="content-card-title">
        <ion-icon :icon="icons.server"></ion-icon>
        Sesiones activas
      </h3>
      <ion-button
        v-if="hasOtherSessions"
        fill="outline"
        size="small"
        color="danger"
        class="revoke-others-btn"
        :disabled="loading"
        @click="confirmRevokeOthers"
      >
        <ion-icon :icon="icons.logOut" slot="start"></ion-icon>
        Cerrar otras
      </ion-button>
    </div>

    <p class="card-desc">
      Dispositivos con una sesión iniciada en tu cuenta. Si ves uno que no
      reconoces, ciérralo y cambia tu contraseña.
    </p>

    <div v-if="loading" class="loading-state">
      <ion-spinner name="crescent"></ion-spinner>
    </div>

    <p v-else-if="sessions.length === 0" class="empty-state">
      No hay sesiones activas registradas.
    </p>

    <div v-else class="session-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ current: session.is_current }"
      >
        <div class="session-info">
          <div class="session-icon">
            <ion-icon :icon="session.is_current ? icons.globe : icons.phone_portrait"></ion-icon>
          </div>
          <div class="session-text">
            <span class="session-name">
              {{ session.device_name || 'Dispositivo desconocido' }}
              <ion-chip v-if="session.is_current" color="primary" size="small">Este dispositivo</ion-chip>
            </span>
            <span class="session-meta">
              <ion-icon :icon="icons.globe"></ion-icon>
              {{ session.ip_address || 'IP desconocida' }}
            </span>
            <span class="session-meta">
              <ion-icon :icon="icons.info"></ion-icon>
              Última actividad: {{ formatDate(session.last_activity) }}
            </span>
            <span v-if="session.user_agent" class="session-ua">{{ session.user_agent }}</span>
          </div>
        </div>

        <ion-button
          v-if="!session.is_current"
          fill="clear"
          size="small"
          color="danger"
          class="revoke-btn"
          :disabled="loading || revokingId === session.id"
          @click="confirmRevoke(session)"
        >
          <ion-spinner v-if="revokingId === session.id" name="dots" slot="start"></ion-spinner>
          Cerrar
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
          <ion-icon :icon="icons.logOut" size="large"></ion-icon>
        </div>
        <p class="confirm-text">{{ confirmMessage }}</p>
        <div class="modal-actions">
          <ion-button fill="outline" @click="closeConfirm">Cancelar</ion-button>
          <ion-button color="danger" :disabled="loading" @click="executeRevoke">
            <ion-spinner v-if="loading" name="crescent" slot="start"></ion-spinner>
            Cerrar sesión
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

const icons = inject('icons', {})

const sessions = ref([])
const loading = ref(false)
const revokingId = ref(null)

const isConfirmOpen = ref(false)
const confirmTitle = ref('')
const confirmMessage = ref('')
// null = revocar todas menos la actual; string = revocar esa sesión
const pendingAction = ref(null)

const hasOtherSessions = computed(() => sessions.value.some(s => !s.is_current))

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

const fetchSessions = async () => {
  loading.value = true
  try {
    const response = await API.get(API.SESSIONS)
    sessions.value = Array.isArray(response) ? response : (response?.results || [])
  } catch (err) {
    console.error('Error al cargar las sesiones:', err)
    await showToast('No se pudieron cargar las sesiones activas.')
  } finally {
    loading.value = false
  }
}

const confirmRevoke = (session) => {
  pendingAction.value = session.id
  confirmTitle.value = 'Cerrar sesión'
  confirmMessage.value =
    `Se cerrará la sesión de "${session.device_name || 'este dispositivo'}" ` +
    `(${session.ip_address || 'IP desconocida'}). Necesitarás volver a iniciar sesión ahí.`
  isConfirmOpen.value = true
}

const confirmRevokeOthers = () => {
  pendingAction.value = null
  const count = sessions.value.filter(s => !s.is_current).length
  confirmTitle.value = 'Cerrar otras sesiones'
  confirmMessage.value =
    `Se cerrarán ${count} ${count === 1 ? 'sesión activa' : 'sesiones activas'} ` +
    'en otros dispositivos. Solo se mantendrá la sesión de este dispositivo.'
  isConfirmOpen.value = true
}

const closeConfirm = () => {
  isConfirmOpen.value = false
  pendingAction.value = null
}

const executeRevoke = async () => {
  const action = pendingAction.value
  const isSingle = typeof action === 'string'

  loading.value = true
  if (isSingle) revokingId.value = action

  try {
    if (isSingle) {
      await API.post(API.SESSIONS_REVOKE(action), {})
    } else {
      await API.post(API.SESSIONS_REVOKE_OTHERS, {})
    }
    closeConfirm()
    await fetchSessions()
    await showToast(isSingle ? 'Sesión cerrada.' : 'Las otras sesiones fueron cerradas.', 'success')
  } catch (err) {
    console.error('Error al revocar sesiones:', err)
    closeConfirm()
    await showToast('No se pudo cerrar la sesión. Inténtalo de nuevo.')
  } finally {
    loading.value = false
    revokingId.value = null
  }
}

onMounted(fetchSessions)
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

.revoke-others-btn {
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

.session-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
}

.session-item.current {
  border-color: var(--ion-color-primary);
  background: rgba(37, 99, 235, 0.04);
}

.session-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.session-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ion-color-light, #f3f4f6);
  color: var(--ion-color-medium);
  font-size: 1.1rem;
}

.session-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.session-name {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ion-text-color);
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--ion-color-medium);
}

.session-meta ion-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}

.session-ua {
  font-size: 0.72rem;
  color: var(--ion-color-medium);
  opacity: 0.75;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.revoke-btn {
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

  .session-item {
    flex-direction: column;
    align-items: stretch;
  }

  .revoke-btn {
    align-self: flex-end;
  }
}
</style>
