<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Registros de auditoría</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${totalCount} ${totalCount === 1 ? 'registro encontrado' : 'registros encontrados'}` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Desktop controls -->
        <div v-if="!isMobile" class="table-controls">
          <ion-searchbar v-model="searchText" placeholder="Buscar en object_repr, cambios, actor..."
            @ionInput="handleSearchInput" show-clear-button="focus" class="custom"></ion-searchbar>
          <div class="desktop-filter-row">
            <label class="filter-field">
              <span>Acción</span>
              <ion-select v-model="actionFilter" placeholder="Seleccionar acción" @ionChange="triggerFetch" class="filter-select">
                <ion-select-option :value="0">Crear</ion-select-option>
                <ion-select-option :value="1">Actualizar</ion-select-option>
                <ion-select-option :value="2">Eliminar</ion-select-option>
                <ion-select-option :value="3">Acceso</ion-select-option>
              </ion-select>
            </label>
            <label class="filter-field">
              <span>Actor (id o email)</span>
              <ion-input v-model="actorFilter" placeholder="user@example.com" @ionInput="handleSearchInput" class="filter-input"></ion-input>
            </label>
            <label class="filter-field">
              <span>App</span>
              <ion-select v-model="appFilter" placeholder="Seleccionar app" @ionChange="handleAppChange" class="filter-select">
                <ion-select-option value="">Todos</ion-select-option>
                <ion-select-option v-for="a in appOptions" :key="a.value" :value="a.value">{{ a.label }}</ion-select-option>
              </ion-select>
            </label>
            <label class="filter-field">
              <span>Modelo</span>
              <ion-select v-model="modelFilter" placeholder="Seleccionar modelo" @ionChange="triggerFetch" class="filter-select"
                :disabled="!appFilter">
                <ion-select-option value="">Todos</ion-select-option>
                <ion-select-option v-for="m in modelOptions" :key="m.model_name" :value="m.model_name">{{ m.label }}</ion-select-option>
              </ion-select>
            </label>
            <label class="filter-field">
              <span>Object PK</span>
              <ion-input v-model="objectPkFilter" placeholder="123" @ionInput="handleSearchInput" class="filter-input"></ion-input>
            </label>
            <label class="filter-field">
              <span>Desde</span>
              <input v-model="startDate" type="datetime-local" @change="triggerFetch" class="date-input" />
            </label>
            <label class="filter-field">
              <span>Hasta</span>
              <input v-model="endDate" type="datetime-local" @change="triggerFetch" class="date-input" />
            </label>
            <div class="filter-actions">
              <QuickControl type="audit" :toRefresh="true" :toClear="true" @refresh="fetchLogs" @clear="clearFilters" />
            </div>
          </div>
        </div>

        <!-- Mobile: single Filters button -->
        <div v-else class="mobile-controls">
          <ion-button @click="openFiltersModal" fill="outline" color="primary">
            <ion-icon :icon="icons.options" slot="start"></ion-icon>
            Filtros
          </ion-button>
          <QuickControl type="audit" :toRefresh="true" :toClear="true" @refresh="fetchLogs" @clear="clearFilters" />
        </div>

        <!-- Error state -->
        <div v-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchLogs" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Body -->
        <div v-else>
          <!-- Empty -->
          <div v-if="!loading && paginatedItems.length === 0" class="empty-container">
            <ion-icon :icon="icons.document" size="large" color="medium"></ion-icon>
            <p>No se encontraron registros con los filtros actuales.</p>
          </div>

          <!-- Desktop table -->
          <div v-else-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
              <ion-row class="table-header">
                <ion-col size="2"><strong>Fecha</strong></ion-col>
                <ion-col size="1.5"><strong>Acción</strong></ion-col>
                <ion-col size="2"><strong>Actor</strong></ion-col>
                <ion-col size="1"><strong>App</strong></ion-col>
                <ion-col size="1.5"><strong>Modelo</strong></ion-col>
                <ion-col size="2"><strong>Objeto</strong></ion-col>
                <ion-col size="1"><strong>IP</strong></ion-col>
                <ion-col size="1"><strong>Detalle</strong></ion-col>
              </ion-row>
              <ion-row v-if="loading" class="row-loading">
                <ion-col class="row-loading-col">
                  <ion-spinner name="crescent"></ion-spinner>
                  <span>Cargando...</span>
                </ion-col>
              </ion-row>
              <template v-else>
                <ion-row v-for="log in paginatedItems" :key="log.id" class="log-row" @click="openDetail(log)">
                  <ion-col size="2">{{ formatTimestamp(log.timestamp) }}</ion-col>
                  <ion-col size="1.5">
                    <ion-chip :color="actionColor(log.action)" size="small" class="action-chip">
                      {{ actionLabel(log.action) || log.action_name }}
                    </ion-chip>
                  </ion-col>
                  <ion-col size="2" class="cell-truncate">{{ log.actor_details?.username || '-' }}</ion-col>
                  <ion-col size="1">{{ log.app || '-' }}</ion-col>
                  <ion-col size="1.5">{{ log.model || '-' }}</ion-col>
                  <ion-col size="2" class="cell-truncate">{{ log.object_repr || log.object_pk || '-' }}</ion-col>
                  <ion-col size="1">{{ log.remote_addr || '-' }}</ion-col>
                  <ion-col size="1" class="cell-truncate">{{ log.detail || '-' }}</ion-col>
                </ion-row>
              </template>
            </ion-grid>

            <!-- Pagination -->
            <div class="pagination">
              <span class="page-size">
                <span class="page-size-label">Filas:</span>
                <select :value="itemsPerPage" class="items-per-page-select" @change="setPageSize(Number($event.target.value))">
                  <option :value="10">10</option>
                  <option :value="25">25</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </span>
              <ion-button fill="clear" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
                <ion-icon :icon="icons.chevronBack" slot="icon-only"></ion-icon>
              </ion-button>
              <span class="page-info">
                Página {{ currentPage }} de {{ totalPages }}
              </span>
              <ion-button fill="clear" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
                <ion-icon :icon="icons.chevronForward" slot="icon-only"></ion-icon>
              </ion-button>
            </div>
          </div>

          <!-- Mobile list -->
          <div v-else class="mobile-list">
            <div v-if="loading" class="mobile-loading">
              <ion-spinner name="crescent"></ion-spinner>
              <span>Cargando...</span>
            </div>
            <template v-else>
              <div v-for="log in paginatedItems" :key="log.id" class="mobile-card" @click="openDetail(log)">
                <div class="mobile-card-header">
                  <ion-chip :color="actionColor(log.action)" size="small" class="action-chip">
                    {{ actionLabel(log.action) || log.action_name }}
                  </ion-chip>
                  <span class="mobile-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
                </div>
                <div class="mobile-card-body">
                  <strong>{{ log.object_repr || log.model || '-' }}</strong>
                  <span class="mobile-meta">
                    {{ log.actor || '-' }} · {{ log.app || '-' }} · {{ log.model || '-' }}
                  </span>
                  <span v-if="log.remote_addr" class="mobile-meta">IP: {{ log.remote_addr }}</span>
                </div>
              </div>
            </template>

            <div class="pagination">
              <span class="page-size">
                <span class="page-size-label">Filas:</span>
                <select :value="itemsPerPage" class="items-per-page-select" @change="setPageSize(Number($event.target.value))">
                  <option :value="10">10</option>
                  <option :value="25">25</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </span>
              <ion-button fill="clear" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
                <ion-icon :icon="icons.chevronBack" slot="icon-only"></ion-icon>
              </ion-button>
              <span class="page-info">
                Página {{ currentPage }} de {{ totalPages }}
              </span>
              <ion-button fill="clear" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
                <ion-icon :icon="icons.chevronForward" slot="icon-only"></ion-icon>
              </ion-button>
            </div>
          </div>
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Mobile Filters Modal -->
    <ion-modal :is-open="isFiltersModalOpen" @did-dismiss="closeFiltersModal" class="filters-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Filtros</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeFiltersModal">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
        <div class="filters-modal-content">
          <ion-searchbar v-model="searchText" placeholder="Buscar..." @ionInput="handleSearchInput"
            show-clear-button="focus" class="custom"></ion-searchbar>
          <label class="filter-field full">
            <span>Acción</span>
            <ion-select v-model="actionFilter" placeholder="Seleccionar acción" @ionChange="triggerFetch">
              <ion-select-option :value="0">Crear</ion-select-option>
              <ion-select-option :value="1">Actualizar</ion-select-option>
              <ion-select-option :value="2">Eliminar</ion-select-option>
              <ion-select-option :value="3">Acceso</ion-select-option>
            </ion-select>
          </label>
          <label class="filter-field full">
            <span>Actor (id o email)</span>
            <ion-input v-model="actorFilter" placeholder="mail@example.com" @ionInput="handleSearchInput"></ion-input>
          </label>
          <label class="filter-field full">
            <span>App</span>
            <ion-select v-model="appFilter" placeholder="Seleccionar app" @ionChange="handleAppChange">
              <ion-select-option value="">Todos</ion-select-option>
              <ion-select-option v-for="a in appOptions" :key="a.value" :value="a.value">{{ a.label }}</ion-select-option>
            </ion-select>
          </label>
          <label class="filter-field full">
            <span>Modelo</span>
            <ion-select v-model="modelFilter" placeholder="Seleccionar modelo" @ionChange="triggerFetch" :disabled="!appFilter">
              <ion-select-option value="">Todos</ion-select-option>
              <ion-select-option v-for="m in modelOptions" :key="m.model_name" :value="m.model_name">{{ m.label }}</ion-select-option>
            </ion-select>
          </label>
          <label class="filter-field full">
            <span>Object PK</span>
            <ion-input v-model="objectPkFilter" placeholder="123" @ionInput="handleSearchInput"></ion-input>
          </label>
          <label class="filter-field full">
            <span>Desde</span>
            <input v-model="startDate" type="datetime-local" @change="triggerFetch" class="date-input-full" />
          </label>
          <label class="filter-field full">
            <span>Hasta</span>
            <input v-model="endDate" type="datetime-local" @change="triggerFetch" class="date-input-full" />
          </label>
        </div>
    </ion-modal>

    <!-- Log Detail Modal -->
    <ion-modal :is-open="selectedLog !== null" @did-dismiss="closeDetail" class="detail-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Detalle de auditoría</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeDetail">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <template v-if="selectedLog">
          <!-- Hero banner -->
          <div class="audit-header">
            <div class="audit-header-left">
              <div class="audit-icon-wrapper">
                <ion-icon :icon="icons.shield"></ion-icon>
              </div>
              <div class="audit-title-section">
                <h2 class="audit-name">{{ selectedLog.object_repr || 'Registro de auditoría' }}</h2>
                <div class="audit-meta">
                  <ion-chip :color="actionColor(selectedLog.action)" size="small" class="action-chip">
                    {{ actionLabel(selectedLog.action) || selectedLog.action_name }}
                  </ion-chip>
                  <span class="audit-time">
                    <ion-icon :icon="icons.time"></ion-icon>
                    {{ formatTimestamp(selectedLog.timestamp) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- General information -->
          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.info" color="primary"></ion-icon>
                Información General
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <div class="info-grid">
                <div class="info-item">
                  <label class="info-label">Actor</label>
                  <p class="info-value">{{ selectedLog.actor || '-' }}</p>
                </div>
                <div class="info-item">
                  <label class="info-label">App</label>
                  <p class="info-value">{{ selectedLog.app || '-' }}</p>
                </div>
                <div class="info-item">
                  <label class="info-label">Modelo</label>
                  <p class="info-value">{{ selectedLog.model || '-' }}</p>
                </div>
                <div class="info-item">
                  <label class="info-label">Object PK</label>
                  <p class="info-value info-mono">{{ selectedLog.object_pk || '-' }}</p>
                </div>
                <div class="info-item full-width">
                  <label class="info-label">Objeto</label>
                  <p class="info-value">{{ selectedLog.object_repr || '-' }}</p>
                </div>
                <div class="info-item">
                  <label class="info-label">IP</label>
                  <p class="info-value info-mono">{{ selectedLog.remote_addr || '-' }}</p>
                </div>
              </div>
            </ion-card-content>
          </ion-card>

          <!-- JSON payload cards -->
          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.code" color="primary"></ion-icon>
                Cambios
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <pre class="json-block">{{ prettyJson(selectedLog.formatted_changes) }}</pre>
            </ion-card-content>
          </ion-card>

          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.terminal" color="primary"></ion-icon>
                Datos serializados
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <pre class="json-block">{{ prettyJson(selectedLog.serialized_data) }}</pre>
            </ion-card-content>
          </ion-card>

          <ion-card v-if="selectedLog.additional_data" class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.library" color="primary"></ion-icon>
                Datos adicionales
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <pre class="json-block">{{ prettyJson(selectedLog.additional_data) }}</pre>
            </ion-card-content>
          </ion-card>

          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.terminal" color="primary"></ion-icon>
                Cambios crudos
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <pre class="json-block">{{ selectedLog.changes }}</pre>
            </ion-card-content>
          </ion-card>
        </template>

        <!-- Fallback if no data -->
        <div v-else class="modal-empty">
          <p>No hay datos disponibles</p>
        </div>
      </ion-content>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { useServerPagination } from '@composables/Tables/useServerPagination.js'
import QuickControl from '@components/operators/quickControl.vue'

const authStore = useAuthStore()
const icons = inject('icons', {})
const { isMobile } = useResponsiveView(768)

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const selectedLog = ref(null)
const isFiltersModalOpen = ref(false)

const searchText = ref('')
const actionFilter = ref(null)
const actorFilter = ref('')
const appFilter = ref('')
const modelFilter = ref('')
const objectPkFilter = ref('')
const startDate = ref('')
const endDate = ref('')
const appsMeta = ref([])

let debounceTimer = null

const appOptions = computed(() =>
  appsMeta.value.map((a) => ({ value: a.app_label, label: a.verbose_name || a.app_label }))
)

const modelOptions = computed(() => {
  const app = appsMeta.value.find((a) => a.app_label === appFilter.value)
  return (app?.models || []).map((m) => ({
    model_name: m.model_name,
    label: m.verbose_name || m.object_name || m.model_name
  }))
})

const loadMeta = async () => {
  try {
    const response = await API.get(API.APPS)
    const payload = Array.isArray(response) ? response[0] : response
    appsMeta.value = Array.isArray(payload?.apps) ? payload.apps : []
  } catch (err) {
    console.error('Error cargando apps para filtros de auditoría:', err)
  }
}

const handleAppChange = () => {
  modelFilter.value = ''
  triggerFetch()
}

onMounted(() => {
  loadMeta()
})

const endpoint = computed(() =>
  authStore.isSuperUser ? API.AUDIT : API.TENANT_AUDIT
)

const formatTimestamp = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

const actionLabel = (action) => {
  const labels = { 0: 'Crear', 1: 'Actualizar', 2: 'Eliminar', 3: 'Acceso' }
  return labels[action] || null
}

const actionColor = (action) => {
  const colors = { 0: 'success', 1: 'primary', 2: 'danger', 3: 'medium' }
  return colors[action] || 'medium'
}

const prettyJson = (value) => {
  if (value === null || value === undefined || value === '') return '(vacío)'
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

const buildQuery = () => {
  const params = new URLSearchParams()
  if (actionFilter.value !== null && actionFilter.value !== '') params.set('action', actionFilter.value)
  if (searchText.value.trim()) params.set('search', searchText.value.trim())
  if (actorFilter.value.trim()) params.set('actor', actorFilter.value.trim())
  if (appFilter.value.trim()) params.set('app', appFilter.value.trim())
  if (modelFilter.value.trim()) params.set('model', modelFilter.value.trim())
  if (objectPkFilter.value.trim()) params.set('object_pk', objectPkFilter.value.trim())
  if (startDate.value) {
    const iso = new Date(startDate.value).toISOString()
    if (!Number.isNaN(new Date(iso).getTime())) params.set('start_date', iso)
  }
  if (endDate.value) {
    const iso = new Date(endDate.value).toISOString()
    if (!Number.isNaN(new Date(iso).getTime())) params.set('end_date', iso)
  }
  params.set('limit', itemsPerPage.value)
  params.set('offset', offset.value)
  return params.toString()
}

const fetchLogs = async (silent = false) => {
  if (!silent) {
    loading.value = true
    error.value = null
  }
  try {
    const qs = buildQuery()
    const url = qs ? `${endpoint.value}?${qs}` : endpoint.value
    const response = await API.get(url)
    // API.get wraps object responses in [obj]; paginated bodies carry data in .results
    const payload = Array.isArray(response) ? response[0] : response
    logs.value = payload?.results ?? []
    setTotal(payload?.count)
  } catch (err) {
    error.value = err.message || 'Error al cargar registros de auditoría'
    logs.value = []
  } finally {
    loading.value = false
  }
}

const handleSearchInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    triggerFetch()
  }, 400)
}

const triggerFetch = () => {
  resetToFirstPage()
  fetchLogs()
}

const clearFilters = () => {
  searchText.value = ''
  actionFilter.value = null
  actorFilter.value = ''
  appFilter.value = ''
  modelFilter.value = ''
  objectPkFilter.value = ''
  startDate.value = ''
  endDate.value = ''
  resetToFirstPage()
  fetchLogs()
}

const openDetail = (log) => {
  selectedLog.value = log
}

const closeDetail = () => {
  selectedLog.value = null
}

const openFiltersModal = () => {
  isFiltersModalOpen.value = true
}

const closeFiltersModal = () => {
  isFiltersModalOpen.value = false
}

const { currentPage, itemsPerPage, totalPages, offset, setTotal, changePage, setPageSize, resetToFirstPage } = useServerPagination({ fetchFn: fetchLogs, pageSize: 10 })
const paginatedItems = computed(() => logs.value)

defineExpose({ fetchLogs })
</script>

<style scoped>
.table-card {
  margin: 16px;
}

ion-card-header {
  padding-bottom: 8px;
}

ion-card-subtitle {
  color: var(--ion-color-medium);
}

.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.row-loading-col {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 28px 0;
  color: var(--ion-color-medium);
}

.mobile-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 28px 0;
  color: var(--ion-color-medium);
}

.table-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.desktop-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.filter-select,
.filter-input,
.date-input {
  height: 56px;
  box-sizing: border-box;
  min-width: 150px;
  max-width: 220px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  background: var(--ion-card-background, #fff);
}

.filter-select,
.filter-input {
  --padding-top: 8px;
  --padding-bottom: 8px;
}

.filter-select {
  --padding-start: 12px;
  --padding-end: 32px;
  --placeholder-opacity: 0.9;
}

.filter-select::part(icon),
.filter-field.full ion-select::part(icon) {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.filter-input {
  --padding-start: 12px;
  --padding-end: 12px;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 150px;
  max-width: 220px;
}

.filter-field.full {
  max-width: none;
  margin-bottom: 12px;
}

.filter-field.full ion-select,
.filter-field.full ion-input,
.filter-field.full .date-input-full {
  width: 100%;
  height: 48px;
  box-sizing: border-box;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  background: var(--ion-card-background, #fff);
  --padding-start: 12px;
  --padding-end: 32px;
  --placeholder-opacity: 0.9;
}

.filter-field span {
  font-size: 0.72rem;
  color: var(--ion-color-medium);
  padding-left: 4px;
}

.date-input {
  padding: 0 12px;
  font-size: 0.9rem;
  width: 100%;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.filter-actions ion-button {
  height: 44px;
  margin: 0;
}

.mobile-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  background: transparent;
  padding: 0;
}

.table-header {
  background: var(--ion-color-light-tint, #f3f4f6);
  border-bottom: 2px solid var(--ion-color-medium);
  font-weight: 600;
}

.log-row {
  cursor: pointer;
  border-bottom: 1px solid var(--ion-color-light-shade, #e5e7eb);
  transition: background-color 0.15s ease;
}

.log-row:hover {
  background: var(--ion-color-light-tint, #f9fafb);
}

.cell-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.action-chip {
  margin: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}

.page-info {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

.page-size {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-size-label {
  font-size: 0.875rem;
  color: var(--ion-color-medium);
}

.items-per-page-select {
  background: var(--ion-background-color, transparent);
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  padding: 6px 32px 6px 12px;
  font-size: 0.875rem;
  color: var(--ion-text-color);
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239ca3af' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 12px;
  transition: all 0.2s;
}

.items-per-page-select:hover {
  border-color: var(--ion-color-primary);
}

.items-per-page-select:focus {
  border-color: var(--ion-color-primary);
  background-color: rgba(var(--ion-color-primary-rgb), 0.05);
}

.mobile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mobile-card {
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
  padding: 12px;
  background: var(--ion-card-background, #fff);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.mobile-card:hover {
  background: var(--ion-color-light-tint, #f9fafb);
}

.mobile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.mobile-timestamp {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.mobile-card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-meta {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
}

.filters-modal {
  --width: 480px;
  --height: auto;
  --max-height: 90vh;
}

.filters-modal-content {
  padding: 16px 20px 24px;
}

.date-input-full {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  background: var(--ion-card-background, #fff);
  font-size: 0.9rem;
  min-width: 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.detail-modal {
  --width: 680px;
  --height: 85vh;
  --max-height: 90vh;
}

/* Hero banner */
.audit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  background: linear-gradient(135deg, var(--ion-color-primary-tint) 0%, var(--ion-color-primary) 100%);
  color: white;
  border-radius: 12px;
  gap: 20px;
}

.audit-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.audit-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.audit-icon-wrapper ion-icon {
  font-size: 32px;
  color: white;
}

.audit-title-section {
  flex: 1;
  min-width: 0;
}

.audit-name {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: white;
  line-height: 1.3;
  word-break: break-word;
}

.audit-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.audit-meta .action-chip {
  margin: 0;
}

.audit-time {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
}

.audit-time ion-icon {
  font-size: 16px;
}

/* Info cards */
.info-card {
  margin: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.info-card:first-of-type {
  margin-top: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.05rem;
  font-weight: 600;
}

.section-title ion-icon {
  font-size: 22px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ion-color-medium);
  letter-spacing: 0.4px;
  text-transform: uppercase;
}

.info-value {
  font-size: 1rem;
  color: var(--ion-color-dark);
  margin: 0;
  line-height: 1.5;
  word-break: break-word;
}

.info-mono {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  background: var(--ion-color-light);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--ion-color-light-shade);
}

.info-value ion-chip {
  margin: 0;
  font-size: 0.9rem;
}

/* JSON blocks */
.json-block {
  background: var(--ion-color-light, #f3f4f6);
  border-radius: 6px;
  padding: 12px;
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 320px;
  overflow: auto;
}

/* Empty fallback */
.modal-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

@media (min-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 576px) {
  .audit-header {
    padding: 16px;
  }

  .audit-icon-wrapper {
    width: 48px;
    height: 48px;
  }

  .audit-icon-wrapper ion-icon {
    font-size: 26px;
  }

  .audit-name {
    font-size: 1.15rem;
  }

  .info-card {
    margin: 12px 0;
  }
}

@media (max-width: 768px) {
  .table-card {
    margin: 8px;
  }

  .pagination {
    flex-wrap: wrap;
  }
}
</style>
