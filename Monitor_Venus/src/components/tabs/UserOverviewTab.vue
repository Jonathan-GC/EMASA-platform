<template>
  <div class="content-card">
    <h3 class="content-card-title">
      <ion-icon :icon="icons.time"></ion-icon>
      Actividad
    </h3>

    <!-- Initial load -->
    <div v-if="loading && !logs.length" class="activity-state">
      <ion-spinner name="crescent"></ion-spinner>
      <p>Cargando actividad...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="activity-state">
      <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
      <p>{{ error }}</p>
      <ion-button @click="fetchActivity" fill="outline" color="primary">Reintentar</ion-button>
    </div>

    <!-- Empty -->
    <div v-else-if="!logs.length" class="activity-state">
      <ion-icon :icon="icons.time" size="large" color="medium"></ion-icon>
      <p>Aún no hay actividad para mostrar.</p>
      <span class="activity-hint">Los registros de auditoría de este usuario aparecerán aquí.</span>
    </div>

    <!-- Timeline -->
    <div v-else class="timeline-wrap">
      <div v-if="loading" class="timeline-loading-row">
        <ion-spinner name="crescent"></ion-spinner>
        <span>Cargando...</span>
      </div>
      <div v-else class="timeline">
        <div v-for="log in logs" :key="log.id" class="timeline-item">
          <div class="timeline-rail">
            <div class="timeline-icon" :class="`action-${actionColor(log.action)}`">
              <ion-icon :icon="actionIcon(log.action)"></ion-icon>
            </div>
          </div>
          <div class="timeline-body">
            <button class="timeline-row" @click="toggleExpanded(log)">
              <div class="timeline-text">
                <p class="timeline-sentence">{{ buildSentence(log) }}</p>
                <span class="timeline-time" :title="formatFullDate(log.timestamp)">{{ timeAgo(log.timestamp) }}</span>
              </div>
              <ion-icon :icon="expandedIds.has(log.id) ? icons.chevronUp : icons.chevronDown"
                class="timeline-chevron"></ion-icon>
            </button>
            <div v-if="expandedIds.has(log.id)" class="timeline-detail">
              <code>{{ prettyJson(log.detail) }}</code>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="timeline-pagination">
        <ion-button fill="clear" :disabled="currentPage === 1" @click="goToPreviousPage">
          <ion-icon :icon="icons.chevronBack" slot="icon-only"></ion-icon>
        </ion-button>
        <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
        <ion-button fill="clear" :disabled="currentPage === totalPages" @click="goToNextPage">
          <ion-icon :icon="icons.chevronForward" slot="icon-only"></ion-icon>
        </ion-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'
import { useServerPagination } from '@composables/Tables/useServerPagination.js'

const props = defineProps({
  userId: { type: [String, Number], required: true }
})

const authStore = useAuthStore()
const icons = inject('icons', {})

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const expandedIds = ref(new Set())

const endpoint = computed(() =>
  authStore.isSuperUser ? API.AUDIT : API.TENANT_AUDIT
)

const {
  currentPage,
  itemsPerPage,
  offset,
  totalPages,
  setTotal,
  goToNextPage,
  goToPreviousPage
} = useServerPagination({ fetchFn: fetchActivity, pageSize: 10 })

async function fetchActivity() {
  loading.value = true
  error.value = null
  try {
    const qs = new URLSearchParams()
    qs.set('actor', props.userId)
    qs.set('limit', itemsPerPage.value)
    qs.set('offset', offset.value)
    const response = await API.get(`${endpoint.value}?${qs.toString()}`)
    // API.get wraps object responses in [obj]; paginated bodies carry data in .results
    const payload = Array.isArray(response) ? response[0] : response
    logs.value = payload?.results ?? []
    setTotal(payload?.count)
  } catch (err) {
    error.value = err.message || 'No se pudo cargar la actividad'
    logs.value = []
  } finally {
    loading.value = false
  }
}

const actionLabel = (action) => {
  const labels = { 0: 'Crear', 1: 'Actualizar', 2: 'Eliminar', 3: 'Acceso' }
  return labels[action] || null
}

const actionColor = (action) => {
  const colors = { 0: 'success', 1: 'primary', 2: 'danger', 3: 'medium' }
  return colors[action] || 'medium'
}

const actionIcon = (action) => {
  const map = { 0: icons.add, 1: icons.edit, 2: icons.delete, 3: icons.key }
  return map[action] || icons.document
}

const buildSentence = (log) => {
  const objectName = log.object_repr || (log.model ? `${log.model} #${log.object_pk}` : '')
  if (log.action === 3) {
    return objectName ? `Acceso a «${objectName}»` : 'Acceso al sistema'
  }
  const verb = { 0: 'Creó', 1: 'Actualizó', 2: 'Eliminó' }[log.action]
  if (!verb) return objectName ? `Registro en «${objectName}»` : 'Registro de actividad'
  return objectName ? `${verb} «${objectName}»` : `${verb} un registro`
}

const timeAgo = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const minutes = Math.floor((Date.now() - d.getTime()) / 60000)
  if (minutes < 1) return 'ahora mismo'
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `hace ${days} día${days === 1 ? '' : 's'}`
  return d.toLocaleDateString()
}

const formatFullDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

const prettyJson = (value) => {
  if (value === null || value === undefined || value === '') return '(sin cambios registrados)'
  let parsed = value
  if (typeof value === 'string') {
    try {
      parsed = JSON.parse(value)
    } catch {
      return value
    }
  }
  try {
    return JSON.stringify(parsed, null, 2)
  } catch {
    return String(value)
  }
}

const toggleExpanded = (log) => {
  const next = new Set(expandedIds.value)
  if (next.has(log.id)) next.delete(log.id)
  else next.add(log.id)
  expandedIds.value = next
}

onMounted(() => {
  fetchActivity()
})
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

.activity-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.activity-state p {
  margin: 0;
  font-size: 0.95rem;
}

.activity-hint {
  font-size: 0.8rem;
  opacity: 0.7;
}

.timeline-wrap {
  display: flex;
  flex-direction: column;
}

.timeline-loading-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--ion-color-medium);
  font-size: 0.85rem;
}

.timeline-item {
  display: flex;
  gap: 14px;
}

.timeline-item:not(:last-child) {
  padding-bottom: 20px;
}

.timeline-rail {
  position: relative;
  display: flex;
  justify-content: center;
}

.timeline-item:not(:last-child) .timeline-rail::after {
  content: '';
  position: absolute;
  top: 36px;
  bottom: 0;
  left: 50%;
  width: 2px;
  transform: translateX(-50%);
  background: var(--ion-color-light-shade, #e5e7eb);
}

.timeline-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.05rem;
  flex-shrink: 0;
}

.action-success {
  background: var(--ion-color-success);
}

.action-primary {
  background: var(--ion-color-primary);
}

.action-danger {
  background: var(--ion-color-danger);
}

.action-medium {
  background: var(--ion-color-medium);
}

.timeline-body {
  flex: 1;
  min-width: 0;
}

.timeline-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  background: none;
  border: none;
  padding: 8px 0;
  cursor: pointer;
  text-align: left;
  color: var(--ion-text-color);
}

.timeline-text {
  flex: 1;
  min-width: 0;
}

.timeline-sentence {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 500;
  word-break: break-word;
}

.timeline-time {
  font-size: 0.78rem;
  color: var(--ion-color-medium);
}

.timeline-chevron {
  font-size: 1.1rem;
  color: var(--ion-color-medium);
  flex-shrink: 0;
}

.timeline-detail {
  margin: 4px 0 8px;
  padding: 10px 12px;
  background: var(--ion-color-light, #f3f4f6);
  border-radius: 8px;
  overflow-x: auto;
}

.timeline-detail code {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--ion-text-color);
  white-space: pre-wrap;
  word-break: break-word;
}

.timeline-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light-shade, #e5e7eb);
}

.page-info {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
}

@media (max-width: 768px) {
  .content-card {
    padding: 16px;
  }
}
</style>
