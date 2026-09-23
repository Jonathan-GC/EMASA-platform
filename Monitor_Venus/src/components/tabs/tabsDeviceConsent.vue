<template>
  <div class="consent-tab">
    <!-- Header -->
    <div class="header">
      <div class="header-title">
        <ion-back-button default-href="/home"></ion-back-button>
        <h1>
          <ion-icon :icon="icons.shield" size="large"></ion-icon>
          Consentimiento de IA
        </h1>
      </div>
    </div>

    <!-- Cargando -->
    <div v-if="loading" class="consent-loading">
      <ion-spinner name="crescent"></ion-spinner>
      <p>Consultando consentimiento...</p>
    </div>

    <template v-else>
      <!-- Avisos no bloqueantes (permisos / error de lectura) -->
      <ion-card v-if="consentError" class="consent-warning-card">
        <ion-card-content>
          <ion-icon :icon="icons.shield" slot="start"></ion-icon>
          {{ consentError }}
        </ion-card-content>
      </ion-card>

      <!-- Estado actual -->
      <ion-card class="consent-status-card">
        <ion-card-header>
          <div class="card-header-content">
            <div class="card-title-section">
              <ion-card-title>Estado del consentimiento</ion-card-title>
              <ion-badge :color="statusMeta.color" class="status-badge">{{ statusMeta.label }}</ion-badge>
            </div>
          </div>
        </ion-card-header>
        <ion-card-content>
          <div v-if="consent" class="consent-details">
            <div class="detail-row">
              <span class="detail-label">Versión</span>
              <span class="detail-value">v{{ consent.version }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Términos</span>
              <span class="detail-value">{{ consent.terms_version }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Otorgado por</span>
              <span class="detail-value">{{ consent.granted_by_username || '—' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Fecha</span>
              <span class="detail-value">{{ fmt(consent.granted_at) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Variables</span>
              <span class="detail-value">{{ consentedSummary }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Firma</span>
              <code class="detail-value signature">{{ truncateSignature(consent.device_signature) }}</code>
            </div>
            <div v-if="consent.status === 'REVOKED'" class="detail-row">
              <span class="detail-label">Revocado por</span>
              <span class="detail-value">{{ consent.revoked_by_username || '—' }} — {{ fmt(consent.revoked_at) }}</span>
            </div>
            <div v-if="consent.status === 'REVOKED' && consent.revocation_reason" class="detail-row">
              <span class="detail-label">Motivo</span>
              <span class="detail-value">{{ consent.revocation_reason }}</span>
            </div>
          </div>
          <div v-else class="consent-empty">
            <p>
              Este dispositivo aún no cuenta con un consentimiento activo
              para compartir sus variables con modelos de IA.
            </p>
          </div>
        </ion-card-content>
      </ion-card>

      <!-- Otorgar / actualizar consentimiento -->
      <ion-card v-if="canManage" class="consent-form-card">
        <ion-card-header>
          <ion-card-title>{{ consent ? 'Actualizar consentimiento' : 'Otorgar consentimiento' }}</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <p class="form-hint">
            Selecciona las variables del dispositivo que el tenant autoriza
            compartir para entrenamiento de modelos de IA.
          </p>

          <div v-if="consentableMeasurements.length" class="measurement-options">
            <ion-item v-for="m in consentableMeasurements" :key="m.id" class="measurement-option">
              <ion-label>
                {{ m.label || m.name }}
                <p v-if="m.unit" class="option-unit">{{ m.unit }}</p>
              </ion-label>
              <ion-checkbox :checked="isSelected(m.id)" @ionChange="toggleMeasurement(m.id)"></ion-checkbox>
            </ion-item>
          </div>
          <div v-else class="consent-empty">
            <p>No hay variables disponibles para consentimiento en este dispositivo.</p>
          </div>

          <ion-item class="terms-item">
            <ion-label position="stacked">Versión de términos</ion-label>
            <ion-input v-model="termsVersion" type="text" placeholder="v1.0"></ion-input>
          </ion-item>

          <ion-button
            expand="block"
            color="primary"
            :disabled="submitting || !consentableMeasurements.length"
            @click="acceptConsent"
          >
            <ion-spinner v-if="submitting" name="crescent" slot="start"></ion-spinner>
            {{ submitting ? 'Guardando...' : consent ? 'Actualizar consentimiento' : 'Otorgar consentimiento' }}
          </ion-button>
        </ion-card-content>
      </ion-card>

      <!-- Revocar consentimiento -->
      <ion-card v-if="canManage && consent && consent.status === 'ACTIVE'" class="consent-revoke-card">
        <ion-card-header>
          <ion-card-title>Revocar</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <p class="form-hint">
            Al revocar, el dispositivo dejará de aportar datos para el
            entrenamiento de IA de forma inmediata.
          </p>
          <ion-button expand="block" color="danger" @click="requestRevoke">
            <ion-icon :icon="icons.shield" slot="start"></ion-icon>
            Revocar consentimiento
          </ion-button>
        </ion-card-content>
      </ion-card>

      <!-- Historial -->
      <ion-card class="consent-history-card">
        <ion-card-header>
          <ion-card-title>Historial de consentimiento</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <div v-if="historyLoading" class="consent-loading compact">
            <ion-spinner name="crescent"></ion-spinner>
          </div>
          <div v-else-if="!history.length" class="consent-empty">
            <p>Sin registros de consentimiento anteriores.</p>
          </div>
          <div v-else class="consent-timeline">
            <div v-for="entry in history" :key="entry.id" class="timeline-item">
              <div class="timeline-rail">
                <span class="timeline-dot" :class="'dot-' + (entry.status || 'unknown').toLowerCase()"></span>
              </div>
              <div class="timeline-content">
                <div class="timeline-head">
                  <strong>v{{ entry.version }}</strong>
                  <ion-badge :color="statusColor(entry.status)" class="status-badge">{{ statusLabel(entry.status) }}</ion-badge>
                </div>
                <p class="timeline-terms">Términos: {{ entry.terms_version }}</p>
                <p class="timeline-meta">Otorgado por {{ entry.granted_by_username || '—' }} el {{ fmt(entry.granted_at) }}</p>
                <p v-if="entry.consented_measurement_ids && entry.consented_measurement_ids.length" class="timeline-vars">
                  Variables: {{ entry.consented_measurement_ids.map(measurementLabel).join(', ') }}
                </p>
                <div v-if="entry.status === 'REVOKED'" class="timeline-revoked">
                  <p>Revocado por {{ entry.revoked_by_username || '—' }} el {{ fmt(entry.revoked_at) }}</p>
                  <p v-if="entry.revocation_reason">Motivo: {{ entry.revocation_reason }}</p>
                </div>
              </div>
            </div>
          </div>
        </ion-card-content>
      </ion-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { toastController, alertController } from '@ionic/vue'
import { format } from 'date-fns'
import API from '@/utils/api/api.js'
import { useAuthStore } from '@/stores/authStore'

const props = defineProps({
  deviceId: {
    type: [String, Number],
    default: null
  },
  measurements: {
    type: Array,
    default: () => []
  }
})

const authStore = useAuthStore()
const icons = inject('icons', {})

// Estado
const loading = ref(true)
const consentError = ref(null)
const consent = ref(null)
const history = ref([])
const historyLoading = ref(true)

const termsVersion = ref('v1.0')
const selectedIds = ref([])
const submitting = ref(false)

// Solo administradores del tenant o gestores pueden otorgar/revocar
const canManage = computed(() =>
  authStore.isSuperUser ||
  authStore.isGlobalUser ||
  authStore.isTenantAdmin ||
  authStore.user?.role_type === 'manager'
)

// Variables que el backend marca como sujetas a consentimiento
const consentableMeasurements = computed(() =>
  (props.measurements || []).filter(m => m.require_consent !== false)
)

const statusMeta = computed(() => {
  if (loading.value) return { label: 'Cargando...', color: 'medium' }
  if (!consent.value) return { label: 'Sin consentimiento', color: 'medium' }
  return { label: statusLabel(consent.value.status), color: statusColor(consent.value.status) }
})

const consentedSummary = computed(() => {
  const ids = consent.value?.consented_measurement_ids
  if (!Array.isArray(ids) || !ids.length) return 'Ninguna'
  const labels = ids.map(measurementLabel)
  return labels.length > 4
    ? `${labels.slice(0, 4).join(', ')} y ${labels.length - 4} más`
    : labels.join(', ')
})

const statusColor = (status) => {
  const map = { ACTIVE: 'success', SUPERSEDED: 'warning', REVOKED: 'danger' }
  return map[status] || 'medium'
}

const statusLabel = (status) => {
  const map = { ACTIVE: 'Activo', SUPERSEDED: 'Reemplazado', REVOKED: 'Revocado' }
  return map[status] || status || 'Desconocido'
}

const measurementLabel = (id) => {
  const m = (props.measurements || []).find(x => String(x.id) === String(id))
  return m ? (m.label || m.name || id) : id
}

const fmt = (value) => {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return format(d, "dd/MM/yyyy HH:mm")
}

const truncateSignature = (sig) => {
  if (!sig) return '—'
  return sig.length > 24 ? `${sig.slice(0, 12)}…${sig.slice(-8)}` : sig
}

const toast = async (message, color = 'success') => {
  const t = await toastController.create({ message, duration: 3000, position: 'bottom', color })
  t.present()
}

const isSelected = (id) => selectedIds.value.includes(String(id))

const toggleMeasurement = (id) => {
  const value = String(id)
  selectedIds.value = selectedIds.value.includes(value)
    ? selectedIds.value.filter(v => v !== value)
    : [...selectedIds.value, value]
}

const load = async () => {
  if (!props.deviceId) {
    consentError.value = 'No se pudo identificar el dispositivo.'
    loading.value = false
    return
  }

  loading.value = true
  consentError.value = null
  historyLoading.value = true

  const results = await Promise.allSettled([
    API.get(API.DEVICE_CONSENT(props.deviceId)),
    API.get(API.DEVICE_CONSENT_HISTORY(props.deviceId))
  ])

  const [consentRes, historyRes] = results

  if (consentRes.status === 'fulfilled') {
    consent.value = consentRes.value || null
    selectedIds.value = Array.isArray(consent.value?.consented_measurement_ids)
      ? consent.value.consented_measurement_ids
      : []
    termsVersion.value = consent.value?.terms_version || 'v1.0'
  } else {
    consent.value = null
    selectedIds.value = []
    const reason = consentRes.reason || {}
    const status = reason?.status || reason?.response?.status
    const message = String(reason?.message || '')
    // 404 = sin consentimiento activo (estado normal), no es un error
    if (status === 403 || message.includes('403') || message.includes('permisos')) {
      consentError.value = 'No tienes permisos para consultar el consentimiento de este dispositivo.'
    } else if (status !== 404 && !message.includes('404')) {
      consentError.value = 'No se pudo consultar el consentimiento activo del dispositivo.'
    }
  }

  if (historyRes.status === 'fulfilled') {
    history.value = Array.isArray(historyRes.value) ? historyRes.value : [historyRes.value]
  } else {
    history.value = []
  }

  historyLoading.value = false
  loading.value = false
}

const acceptConsent = async () => {
  if (!canManage.value || !props.deviceId || submitting.value) return
  if (!selectedIds.value.length) {
    toast('Selecciona al menos una variable para compartir.', 'warning')
    return
  }

  submitting.value = true
  try {
    await API.post(API.DEVICE_CONSENT_ACCEPT(props.deviceId), {
      consented_measurement_ids: selectedIds.value,
      terms_version: termsVersion.value || 'v1.0'
    })
    toast('Consentimiento guardado correctamente.')
    await load()
  } catch (error) {
    toast(error?.message || 'No se pudo guardar el consentimiento.', 'danger')
  } finally {
    submitting.value = false
  }
}

const requestRevoke = async () => {
  const alert = await alertController.create({
    header: 'Revocar consentimiento',
    message: 'Indica el motivo por el que se revoca el consentimiento de IA para este dispositivo.',
    inputs: [
      {
        name: 'reason',
        type: 'textarea',
        placeholder: 'Motivo de la revocación'
      }
    ],
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Revocar',
        role: 'destructive',
        handler: async (data) => {
          const reason = (data?.reason || '').trim()
          if (!reason) return false
          try {
            const response = await API.post(API.DEVICE_CONSENT_REVOKE(props.deviceId), { reason })
            toast('Consentimiento revocado.')
            await load()
            return true
          } catch (error) {
            toast(error?.message || 'No se pudo revocar el consentimiento.', 'danger')
            return false
          }
        }
      }
    ]
  })
  await alert.present()
}

onMounted(load)
</script>

<style scoped>
.consent-tab {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header {
  text-align: center;
  margin-bottom: 6px;
}

.header h1 {
  margin: 0 0 4px 0;
  color: #374151;
  font-size: 1.6rem;
  font-weight: 600;
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.status-badge {
  font-size: 0.75rem;
}

.form-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin: 0 0 14px 0;
}

.consent-details .detail-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 7px 0;
  border-bottom: 1px solid #f3f4f6;
}

.consent-details .detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #6b7280;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.detail-value {
  color: #111827;
  font-size: 0.9rem;
  text-align: right;
  word-break: break-word;
}

.detail-value.signature {
  font-size: 0.75rem;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.consent-empty {
  text-align: center;
  color: #6b7280;
  font-size: 0.9rem;
  padding: 10px 0;
}

.consent-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 30px 0;
  color: #6b7280;
}

.consent-loading.compact {
  padding: 14px 0;
}

.consent-warning-card {
  border-left: 4px solid #f59e0b;
}

.consent-warning-card ion-card-content {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #92400e;
  font-size: 0.9rem;
}

.measurement-options {
  margin-bottom: 14px;
}

.measurement-option {
  --padding-start: 8px;
  --inner-padding-end: 8px;
  border-radius: 8px;
  margin-bottom: 4px;
}

.measurement-option .option-unit {
  color: #6b7280;
  font-size: 0.8rem;
}

.terms-item {
  margin-bottom: 14px;
  --padding-start: 8px;
  --inner-padding-end: 8px;
}

.consent-revoke-card {
  border-left: 4px solid #ef4444;
}

.consent-timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 14px;
  padding-bottom: 18px;
  position: relative;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex-shrink: 0;
}

.timeline-item:not(:last-child) .timeline-rail::after {
  content: '';
  position: absolute;
  top: 12px;
  bottom: -6px;
  width: 2px;
  background: #e5e7eb;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  z-index: 1;
}

.timeline-dot.dot-active {
  background: #22c55e;
}

.timeline-dot.dot-superseded {
  background: #f59e0b;
}

.timeline-dot.dot-revoked {
  background: #ef4444;
}

.timeline-dot.dot-unknown {
  background: #9ca3af;
}

.timeline-content {
  flex: 1;
  padding: 2px 0 0 0;
}

.timeline-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.timeline-head strong {
  color: #111827;
}

.timeline-terms,
.timeline-meta {
  margin: 2px 0;
  color: #374151;
  font-size: 0.85rem;
}

.timeline-vars {
  margin: 4px 0;
  color: #6b7280;
  font-size: 0.8rem;
}

.timeline-revoked {
  margin-top: 6px;
  padding: 8px 10px;
  border-left: 3px solid #ef4444;
  background: #fef2f2;
  border-radius: 6px;
  color: #b91c1c;
  font-size: 0.8rem;
}
</style>