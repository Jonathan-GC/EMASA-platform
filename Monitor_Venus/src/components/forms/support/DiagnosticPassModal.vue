<template>
  <ion-page>
    <ion-header class="custom">
      <ion-toolbar>
        <ion-title>Pase de acceso</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="closeModal">
            <ion-icon :icon="icons.close"></ion-icon>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <ion-item class="ticket-summary" lines="none">
        <ion-icon slot="start" :icon="icons.mail"></ion-icon>
        <ion-label>
          <h2>{{ props.ticket.title || '(Sin asunto)' }}</h2>
          <p>Otorga acceso temporal a un técnico sobre el espacio de trabajo del ticket.</p>
        </ion-label>
      </ion-item>

      <ion-note color="warning" class="warning-note">
        <ion-icon :icon="icons.warning"></ion-icon>
        El técnico podrá operar sobre «{{ workspaceName }}» por la duración indicada. El pase inicia en nivel READ, puede mejorarse (READ → EDIT → ADJUST), expira automáticamente y puede revocarse en cualquier momento.
      </ion-note>

      <div v-if="loading" class="ion-text-center ion-padding">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando datos...</p>
      </div>

      <div v-else-if="loadError" class="error-container ion-text-center">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ loadError }}</p>
        <ion-button @click="init" fill="outline">Reintentar</ion-button>
      </div>

      <div v-else>
        <ion-item>
          <ion-label position="stacked">Técnico</ion-label>
          <ion-select
            v-model="technicianId"
            :placeholder="technicians.length ? 'Selecciona un técnico' : 'No hay técnicos disponibles'"
            :disabled="!technicians.length || submitting"
          >
            <ion-select-option v-for="t in technicians" :key="t.id" :value="t.id">
              {{ t.full_name || t.name || `#${t.id}` }}
              <template v-if="t.role"> ({{ t.role }})</template>
            </ion-select-option>
          </ion-select>
        </ion-item>

        <ion-item lines="none" class="workspace-display">
          <ion-icon slot="start" :icon="icons.business"></ion-icon>
          <ion-label>
            <p>Espacio de trabajo del ticket</p>
            <h3>{{ workspaceName }}</h3>
          </ion-label>
        </ion-item>

        <ion-note v-if="!workspaceId" color="danger" class="missing-workspace-note">
          <ion-icon :icon="icons.alertCircle"></ion-icon>
          Este ticket no tiene workspace asignado, por lo que no se puede emitir un pase de acceso.
        </ion-note>

        <ion-item>
          <ion-label position="stacked">Duración (horas)</ion-label>
          <ion-input v-model="durationHours" type="number" min="1" max="720" :disabled="submitting" placeholder="4"></ion-input>
        </ion-item>

        <ion-item>
          <ion-label position="stacked">Motivo</ion-label>
          <ion-textarea v-model="reason" rows="3" :disabled="submitting" placeholder="Motivo del pase de acceso"></ion-textarea>
        </ion-item>

        <div class="ion-padding-top">
          <ion-button
            expand="block"
            :disabled="!technicianId || !workspaceId || !durationHours || submitting"
            @click="confirmGrant"
            color="primary"
          >
            <ion-spinner v-if="submitting" name="crescent" slot="start"></ion-spinner>
            <ion-icon v-else :icon="icons.shield" slot="start"></ion-icon>
            Emitir pase de acceso
          </ion-button>
        </div>

        <div class="divider"></div>

        <div v-if="passesLoading" class="ion-text-center ion-padding">
          <ion-spinner name="dots"></ion-spinner>
          <p>Cargando pases...</p>
        </div>

        <template v-else>
          <!-- Pases activos del ticket -->
          <div v-if="activePasses.length" class="passes-section">
            <h3 class="passes-title">
              <ion-icon :icon="icons.time"></ion-icon>
              Pases activos ({{ activePasses.length }})
            </h3>

            <div v-for="p in activePasses" :key="p.id" class="pass-card">
              <div class="pass-info">
                <div class="pass-header">
                  <span class="pass-tech">{{ p.technician_name || `#${p.technician}` }}</span>
                  <ion-badge class="level-badge" :color="levelColor(p)">{{ levelText(p) }}</ion-badge>
                  <ion-badge class="status-badge" :color="p.is_valid ? 'success' : 'warning'">
                    {{ p.is_valid ? 'ACTIVO' : 'EXPIRADO' }}
                  </ion-badge>
                </div>
                <p class="pass-meta">
                  {{ p.workspace_name || `#${p.workspace}` }} · Expira: {{ formatExpiry(p.expires_at) }}
                </p>
                <p v-if="p.granted_by_name" class="pass-meta">Otorgado por: {{ p.granted_by_name }}</p>
                <p v-if="p.reason" class="pass-meta pass-reason">Motivo: {{ p.reason }}</p>
                <div v-if="p.scopes && p.scopes.length" class="scope-chips">
                  <ion-badge v-for="s in p.scopes" :key="s" class="scope-chip">{{ s }}</ion-badge>
                </div>
              </div>
              <div class="pass-actions">
                <ion-button
                  v-if="canUpgrade(p)"
                  fill="outline"
                  size="small"
                  :disabled="upgradingId === p.id"
                  @click="confirmUpgrade(p)"
                >
                  <ion-spinner v-if="upgradingId === p.id" name="crescent" slot="start"></ion-spinner>
                  <ion-icon v-else :icon="icons.upload" slot="start"></ion-icon>
                  Mejorar
                </ion-button>
                <ion-button
                  v-if="p.is_valid"
                  fill="outline"
                  color="danger"
                  size="small"
                  :disabled="revokingId === p.id"
                  @click="confirmRevoke(p)"
                >
                  <ion-spinner v-if="revokingId === p.id" name="crescent" slot="start"></ion-spinner>
                  <ion-icon v-else :icon="icons.close" slot="start"></ion-icon>
                  Revocar
                </ion-button>
              </div>
            </div>
          </div>

          <p v-else class="no-passes ion-text-center">
            <ion-icon :icon="icons.checkmark"></ion-icon>
            No hay pases activos para este ticket.
          </p>

          <!-- Historial: pases revocados o expirados del ticket -->
          <div v-if="pastPasses.length" class="passes-section history-section">
            <h3 class="passes-title history-title">Historial ({{ pastPasses.length }})</h3>
            <ion-list inset>
              <ion-item v-for="p in pastPasses" :key="p.id">
                <ion-icon slot="start" :icon="icons.person"></ion-icon>
                <ion-label>
                  <h3>{{ p.technician_name || `#${p.technician}` }}</h3>
                  <p>{{ statusText(p) }} · Expira: {{ formatExpiry(p.expires_at) }}</p>
                  <p v-if="p.revoke_reason">Motivo de revocación: {{ p.revoke_reason }}</p>
                </ion-label>
                <ion-badge slot="end" :color="pastStatusColor(p)">{{ statusText(p) }}</ion-badge>
              </ion-item>
            </ion-list>
          </div>
        </template>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import {
  IonPage, IonHeader, IonToolbar, IonTitle, IonContent,
  IonButtons, IonButton, IonIcon, IonItem, IonLabel, IonNote,
  IonSelect, IonSelectOption, IonSpinner, IonTextarea, IonBadge, IonList,
  alertController, actionSheetController, toastController, modalController
} from '@ionic/vue'
import API from '@utils/api/api'

const props = defineProps({
  ticket: {
    type: Object,
    required: true
  }
})

const icons = inject('icons', {})

const technicians = ref([])
const passes = ref([])
const loading = ref(true)
const passesLoading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const revokingId = ref(null)
const upgradingId = ref(null)
// Indica si el modal modificó pases (para que el inbox refresque su indicador)
const hasChanges = ref(false)

// El workspace se toma siempre del ticket; el usuario ya no lo selecciona.
const workspaceId = computed(() => props.ticket?.workspace ?? null)
const workspaceName = computed(() =>
  props.ticket?.workspace_name || (workspaceId.value ? `#${workspaceId.value}` : '—')
)
const technicianId = ref(null)
const durationHours = ref(4)
const reason = ref('')

// Niveles de permiso del pase de acceso (solo se puede mejorar, nunca bajar)
const LEVEL_RANK = { READ: 1, EDIT: 2, ADJUST: 3 }
const LEVEL_COLOR = { READ: 'medium', EDIT: 'warning', ADJUST: 'danger' }
const LEVEL_OPTION_LABELS = {
  EDIT: 'EDIT — Lectura y edición',
  ADJUST: 'ADJUST — Lectura, edición y borrado'
}

const toList = (res) => Array.isArray(res) ? res : (res?.results || res?.data || [])

// Extraer mensaje de error legible (el backend responde {"error": "..."})
const extractError = (err) => {
  const details = err?.details
  if (details && typeof details === 'object') {
    if (typeof details.error === 'string') return details.error
    if (typeof details.detail === 'string') return details.detail
  }
  return err?.message || ''
}

const activePasses = computed(() =>
  passes.value.filter(p => String(p.status || '').toUpperCase() === 'ACTIVE')
)

const pastPasses = computed(() =>
  passes.value.filter(p => String(p.status || '').toUpperCase() !== 'ACTIVE')
)

// Helpers de nivel / estado del pase
const levelText = (p) => String(p?.permission_level || 'READ').toUpperCase()
const levelColor = (p) => LEVEL_COLOR[levelText(p)] || 'medium'
const nextLevels = (p) => {
  const rank = LEVEL_RANK[levelText(p)] || 1
  return Object.keys(LEVEL_RANK).filter(l => LEVEL_RANK[l] > rank)
}
const canUpgrade = (p) => !!p.is_valid && nextLevels(p).length > 0
const statusText = (p) => {
  const s = String(p?.status || '').toUpperCase()
  if (s === 'REVOKED') return 'REVOCADO'
  if (s === 'EXPIRED') return 'EXPIRADO'
  if (!p?.is_valid) return 'EXPIRADO'
  return 'ACTIVO'
}
const pastStatusColor = (p) => String(p?.status || '').toUpperCase() === 'REVOKED' ? 'danger' : 'medium'

const formatExpiry = (iso) => {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

const fetchSupportMembers = async () => {
  const res = await API.get(API.SUPPORT_MEMBERS)
  const members = toList(res).map(m => ({
    id: m.id,
    full_name: m.full_name || m.name || m.username || `User #${m.id}`,
    role: m.role || m.position || m.title || ''
  }))
  const preferred = members.filter(m => /technician|support_agent|technico|tecnico/i.test(m.role || ''))
  technicians.value = preferred.length ? preferred : members
}

// Pases del ticket desde el endpoint dedicado (incluye niveles y scopes)
const fetchPasses = async () => {
  if (props.ticket?.id == null) return
  passesLoading.value = true
  try {
    const endpoint = `${API.HALL_PASSES}?ticket=${encodeURIComponent(props.ticket.id)}`
    const res = await API.get(endpoint)
    passes.value = toList(res)
  } catch (err) {
    console.error('Error fetching hall passes:', err)
  } finally {
    passesLoading.value = false
  }
}

const init = async () => {
  loading.value = true
  loadError.value = ''
  try {
    await fetchSupportMembers()
    if (props.ticket?.id != null) fetchPasses()
  } catch (err) {
    console.error('Error initializing hall pass modal:', err)
    loadError.value = 'No se pudieron cargar los datos necesarios.'
  } finally {
    loading.value = false
  }
}

const showToast = async (message, color = 'success') => {
  const toast = await toastController.create({
    message,
    duration: 3000,
    color,
    position: 'top'
  })
  await toast.present()
}

const confirmGrant = async () => {
  const alert = await alertController.create({
    header: 'Confirmar pase de acceso',
    message: `¿Deseas emitir un pase de acceso de ${durationHours.value} horas sobre «${workspaceName.value}»?`,
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Emitir',
        role: 'confirm',
        handler: () => { grantPass() }
      }
    ]
  })
  await alert.present()
}

const grantPass = async () => {
  submitting.value = true
  try {
    const payload = {
      technician_id: technicianId.value,
      workspace_id: workspaceId.value,
      duration_hours: Number(durationHours.value)
    }
    if ((reason.value || '').trim()) payload.reason = reason.value.trim()

    await API.post(API.GRANT_DIAGNOSTIC_PASS(props.ticket.id), payload)
    hasChanges.value = true
    // Resetear formulario y recargar pases sin cerrar el modal,
    // para poder ver el nuevo pase (READ) y mejorarlo de inmediato.
    technicianId.value = null
    reason.value = ''
    await fetchPasses()
    await showToast('Pase de acceso emitido exitosamente.')
  } catch (err) {
    console.error('Error granting hall pass:', err)
    await showToast(extractError(err) || 'Error al emitir el pase de acceso.', 'danger')
  } finally {
    submitting.value = false
  }
}

// --- Mejorar pase (READ → EDIT → ADJUST) ---

const confirmUpgrade = async (pass) => {
  const options = nextLevels(pass)
  if (!options.length) return
  const sheet = await actionSheetController.create({
    header: 'Mejorar pase de acceso',
    subHeader: `Nivel actual: ${levelText(pass)}`,
    buttons: [
      ...options.map(l => ({
        text: LEVEL_OPTION_LABELS[l] || l,
        handler: () => { confirmUpgradeLevel(pass, l) }
      })),
      { text: 'Cancelar', role: 'cancel' }
    ]
  })
  await sheet.present()
}

const confirmUpgradeLevel = async (pass, newLevel) => {
  const alert = await alertController.create({
    header: `Mejorar a ${newLevel}`,
    message: `${pass.technician_name || 'Este técnico'} pasará de ${levelText(pass)} a ${newLevel}.`,
    inputs: [
      {
        name: 'hours',
        type: 'number',
        min: 1,
        placeholder: 'Extender expiración (horas, opcional)'
      }
    ],
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Mejorar',
        role: 'confirm',
        handler: (data) => { doUpgrade(pass, newLevel, data?.hours) }
      }
    ]
  })
  await alert.present()
}

const doUpgrade = async (pass, newLevel, hours) => {
  upgradingId.value = pass.id
  try {
    const payload = {
      pass_id: pass.id,
      new_permission_level: newLevel
    }
    const parsedHours = parseInt(hours, 10)
    if (Number.isFinite(parsedHours) && parsedHours > 0) payload.duration_hours = parsedHours

    const res = await API.post(API.UPGRADE_HALL_PASS(props.ticket.id), payload)
    hasChanges.value = true
    // La respuesta del API envuelve objetos únicos en un arreglo
    const [updated] = toList(res)
    if (updated?.id) {
      const idx = passes.value.findIndex(p => String(p.id) === String(updated.id))
      if (idx !== -1) passes.value[idx] = updated
      else passes.value.push(updated)
      await showToast(`Pase mejorado a ${levelText(updated)}.`)
    } else {
      await fetchPasses()
      await showToast('Pase mejorado.')
    }
  } catch (err) {
    console.error('Error upgrading hall pass:', err)
    await showToast(extractError(err) || 'Error al mejorar el pase.', 'danger')
  } finally {
    upgradingId.value = null
  }
}

// --- Revocar pase (con motivo opcional) ---

const confirmRevoke = async (pass) => {
  const alert = await alertController.create({
    header: 'Revocar pase',
    message: `¿Estás seguro de que deseas revocar el pase de ${pass.technician_name || 'este técnico'}?`,
    inputs: [
      {
        name: 'reason',
        type: 'text',
        placeholder: 'Motivo de revocación (opcional)'
      }
    ],
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Revocar',
        role: 'confirm',
        handler: (data) => { doRevoke(pass, (data?.reason || '').trim()) }
      }
    ]
  })
  await alert.present()
}

const doRevoke = async (pass, reason) => {
  revokingId.value = pass.id
  try {
    const payload = { pass_id: pass.id }
    if (reason) payload.reason = reason

    await API.post(API.REVOKE_DIAGNOSTIC_PASS(props.ticket.id), payload)
    hasChanges.value = true
    // Recargar para reflejar estado REVOKED (y su motivo) en el historial
    await fetchPasses()
    await showToast('Pase revocado exitosamente.')
  } catch (err) {
    console.error('Error revoking hall pass:', err)
    await showToast(extractError(err) || 'Error al revocar el pase.', 'danger')
  } finally {
    revokingId.value = null
  }
}

const closeModal = () => {
  modalController.dismiss({ changed: hasChanges.value })
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.ticket-summary {
  margin-bottom: 12px;
}

.warning-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: #fff6e6;
  margin-bottom: 12px;
  white-space: normal;
}

.missing-workspace-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  background: var(--ion-color-danger-tint, #fde8e8);
  margin-bottom: 12px;
  white-space: normal;
}

/* Tamaño estándar de icono de aviso: 28px (siempre en el host ion-icon) */
.warning-note ion-icon,
.missing-workspace-note ion-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.workspace-display ion-icon {
  font-size: 28px;
  color: #6b7280;
  margin-inline-end: 12px;
}

.workspace-display h3 {
  font-weight: 600;
  color: #111827;
}

.error-container {
  margin-top: 40px;
}

.error-container ion-icon {
  font-size: 64px;
  opacity: 0.5;
}

.divider {
  height: 0;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  margin: 16px 0;
}

.passes-section {
  margin-top: 4px;
}

.passes-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  color: #111827;
  margin-bottom: 8px;
}

.history-title {
  color: #6b7280;
  font-weight: 500;
}

.history-section {
  margin-top: 16px;
}

.no-passes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: 12px;
}

.pass-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 8px;
  background: #ffffff;
}

.pass-info {
  flex: 1;
  min-width: 0;
}

.pass-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pass-tech {
  font-weight: 600;
  color: #111827;
  font-size: 0.95rem;
}

.pass-meta {
  margin: 4px 0 0;
  font-size: 0.8rem;
  color: #6b7280;
}

.pass-reason {
  font-style: italic;
}

.level-badge,
.status-badge {
  --padding-start: 8px;
  --padding-end: 8px;
  --border-radius: 12px;
  font-size: 0.72rem;
  line-height: 1;
  text-transform: uppercase;
}

.scope-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.scope-chip {
  --padding-start: 8px;
  --padding-end: 8px;
  --border-radius: 12px;
  font-size: 0.7rem;
  line-height: 1;
  text-transform: capitalize;
  background: #eef2ff;
  color: #4338ca;
}

.pass-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  flex-shrink: 0;
}
</style>
