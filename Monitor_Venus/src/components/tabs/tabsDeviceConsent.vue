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

    <ion-card-subtitle class="section-description !mb-1">
      <ion-icon :icon="icons.warning" class="description-icon"></ion-icon>
      <span>
        Selecciona las variables del dispositivo que el tenant autoriza
        compartir para entrenamiento de modelos de IA.
      </span>
    </ion-card-subtitle>

    <!-- Cargando -->
    <div v-if="loading" class="consent-loading">
      <ion-spinner name="crescent"></ion-spinner>
      <p>Consultando consentimiento...</p>
    </div>

    <template v-else>
      <div class="consent-grid">
      <!-- Variables disponibles -->
      <ion-card class="consent-variables-card">
        <ion-card-header>
          <ion-card-title>Variables disponibles</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <div v-if="consentableMeasurements.length" class="measurement-options">
            <ion-item v-for="m in consentableMeasurements" :key="m.id" class="measurement-option">
              <ion-label>{{ m.label || m.name }}</ion-label>
              <ion-checkbox
                :checked="isSelected(m.id)"
                :disabled="!canManage"
                @ionChange="toggleMeasurement(m.id)"
              ></ion-checkbox>
            </ion-item>
          </div>
          <div v-else class="consent-empty">
            <p>No hay variables disponibles para consentimiento en este dispositivo.</p>
          </div>

          <ion-button
            v-if="canManage"
            expand="block"
            color="primary"
            :disabled="submitting || !consentableMeasurements.length"
            @click="acceptConsent"
          >
            <ion-spinner v-if="submitting" name="crescent" slot="start"></ion-spinner>
            {{ submitting ? 'Guardando...' : consent ? 'Actualizar consentimiento' : 'Guardar consentimiento' }}
          </ion-button>

          <p v-if="loadError" class="consent-error">{{ loadError }}</p>
        </ion-card-content>
      </ion-card>

      <!-- Detalles de firma -->
      <ion-card class="consent-signature-card">
        <ion-card-header>
          <ion-card-title>Detalles de firma</ion-card-title>
        </ion-card-header>
        <ion-card-content>
          <div class="detail-row">
            <span class="detail-label">Firma del dispositivo</span>
            <code :title="fullSignature" class="detail-value signature">{{ truncatedSignature }}</code>
          </div>
          <div class="detail-row">
            <span class="detail-label">Versión de términos</span>
            <span class="detail-value">{{ signatureTermsVersion }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Última actualización</span>
            <span class="detail-value">{{ signatureUpdatedAt }}</span>
          </div>
        </ion-card-content>
      </ion-card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { toastController } from '@ionic/vue'
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
const loadError = ref(null)
const consent = ref(null)
const history = ref([])
const selectedIds = ref([])
const submitting = ref(false)

// Solo administradores del tenant o gestores pueden otorgar
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

// Fuente de la tarjeta de firma: consentimiento activo o último registro histórico
const signatureSource = computed(() => consent.value || history.value[0] || null)

const truncatedSignature = computed(() => truncateSignature(signatureSource.value?.device_signature))
const fullSignature = computed(() => signatureSource.value?.device_signature || '—')
const signatureTermsVersion = computed(() => signatureSource.value?.terms_version || '—')
const signatureUpdatedAt = computed(() => (signatureSource.value ? fmt(signatureSource.value.granted_at) : '—'))

const storageKey = () => `device_consent_selection:${props.deviceId}`

const loadStoredSelection = () => {
  try {
    const raw = localStorage.getItem(storageKey())
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const persistSelection = () => {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(selectedIds.value))
  } catch {
    // almacenamiento no disponible
  }
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
  if (!canManage.value) return
  const value = String(id)
  selectedIds.value = selectedIds.value.includes(value)
    ? selectedIds.value.filter(v => v !== value)
    : [...selectedIds.value, value]
  persistSelection()
}

const load = async () => {
  if (!props.deviceId) {
    loadError.value = 'No se pudo identificar el dispositivo.'
    loading.value = false
    return
  }

  loading.value = true
  loadError.value = null

  const results = await Promise.allSettled([
    API.get(API.DEVICE_CONSENT(props.deviceId)),
    API.get(API.DEVICE_CONSENT_HISTORY(props.deviceId))
  ])

  const [consentRes, historyRes] = results

  if (consentRes.status === 'fulfilled') {
    consent.value = consentRes.value || null
    selectedIds.value = Array.isArray(consent.value?.consented_measurement_ids)
      ? consent.value.consented_measurement_ids.map(String)
      : []
  } else {
    consent.value = null
    const reason = consentRes.reason || {}
    const status = reason?.status || reason?.response?.status
    const message = String(reason?.message || '')
    if (status === 403 || message.includes('403') || message.includes('permisos')) {
      loadError.value = 'No tienes permisos para consultar el consentimiento de este dispositivo.'
    } else if (status !== 404 && !message.includes('404')) {
      loadError.value = 'No se pudo consultar el consentimiento activo del dispositivo.'
    }
    // Sin consentimiento activo: conserva la selección guardada localmente
    selectedIds.value = loadStoredSelection()
  }

  if (historyRes.status === 'fulfilled') {
    history.value = Array.isArray(historyRes.value) ? historyRes.value : [historyRes.value]
  } else {
    history.value = []
  }

  // Filtra valores que ya no correspondan a variables del dispositivo
  const validIds = new Set((props.measurements || []).map(m => String(m.id)))
  selectedIds.value = selectedIds.value.filter(id => validIds.has(id))

  persistSelection()
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
      terms_version: consent.value?.terms_version || 'v1.0'
    })
    toast('Consentimiento guardado correctamente.')
    persistSelection()
    await load()
  } catch (error) {
    toast(error?.message || 'No se pudo guardar el consentimiento.', 'danger')
  } finally {
    submitting.value = false
  }
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
  margin-bottom: 2px;
}

.header h1 {
  margin: 0 0 4px 0;
  color: #374151;
  font-size: 1.6rem;
  font-weight: 600;
}

.section-description {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 6px 0;
  line-height: 1.5;
  padding: 12px;
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  text-align: left;
}

.description-icon {
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 2px;
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

.consent-empty {
  text-align: center;
  color: #6b7280;
  font-size: 0.9rem;
  padding: 10px 0;
}

.consent-error {
  margin: 12px 0 0 0;
  color: #b91c1c;
  font-size: 0.85rem;
  text-align: center;
}

.consent-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
}

@media (min-width: 768px) {
  .consent-grid {
    grid-template-columns: 1fr 1fr;
    align-items: start;
  }
}

.consent-variables-card,
.consent-signature-card {
  margin: 0;
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

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 7px 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail-row:last-child {
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
</style>