<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Backups de Base de Datos</ion-card-title>
        <ion-card-subtitle>
          {{ loading && !polling ? 'Cargando...' : `${totalCount} ${totalCount === 1 ? 'backup encontrado' : 'backups encontrados'}` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Controls -->
        <div v-if="!isMobile" class="table-controls">
          <div class="desktop-filter-row">
            <label class="filter-field">
              <span>Estado</span>
              <ion-select v-model="statusFilter" placeholder="Seleccionar estado" @ionChange="triggerFetch" class="filter-select">
                <ion-select-option value="">Todos</ion-select-option>
                <ion-select-option value="PENDING">Pendiente</ion-select-option>
                <ion-select-option value="IN_PROGRESS">En progreso</ion-select-option>
                <ion-select-option value="COMPLETED">Completado</ion-select-option>
                <ion-select-option value="FAILED">Fallido</ion-select-option>
              </ion-select>
            </label>
            <label class="filter-field">
              <span>Tipo de trigger</span>
              <ion-select v-model="triggerTypeFilter" placeholder="Seleccionar trigger" @ionChange="triggerFetch" class="filter-select">
                <ion-select-option value="">Todos</ion-select-option>
                <ion-select-option value="MANUAL_CLI">Manual (CLI)</ion-select-option>
                <ion-select-option value="MANUAL_API">Manual (API)</ion-select-option>
              </ion-select>
            </label>
            <label class="filter-field">
              <span>Ordenar</span>
              <ion-select v-model="orderingFilter" placeholder="Ordenar por" @ionChange="triggerFetch" class="filter-select">
                <ion-select-option value="-created_at">Recientes primero</ion-select-option>
                <ion-select-option value="created_at">Antiguos primero</ion-select-option>
                <ion-select-option value="-size_bytes">Mayor tamaño</ion-select-option>
                <ion-select-option value="size_bytes">Menor tamaño</ion-select-option>
                <ion-select-option value="-started_at">Iniciado (reciente)</ion-select-option>
                <ion-select-option value="started_at">Iniciado (antiguo)</ion-select-option>
                <ion-select-option value="-completed_at">Completado (reciente)</ion-select-option>
                <ion-select-option value="completed_at">Completado (antiguo)</ion-select-option>
              </ion-select>
            </label>
            <div class="filter-actions">
              <QuickControl
                type="backup"
                :toCreate="true"
                :toRefresh="true"
                :toClear="hasFilters"
                @refresh="fetchBackups"
                @clear="clearFilters"
                @itemCreated="fetchBackups"
              />
            </div>
          </div>
        </div>

        <!-- Mobile: controls moved to the floating action buttons -->

        <!-- Error -->
        <div v-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchBackups" fill="outline" color="danger">Reintentar</ion-button>
        </div>

        <!-- Body -->
        <div v-else>
          <!-- Empty -->
          <div v-if="!loading && paginatedItems.length === 0" class="empty-container">
            <ion-icon :icon="icons.cloud" size="large" color="medium"></ion-icon>
            <p>No se encontraron backups con los filtros actuales.</p>
          </div>

          <!-- Desktop table -->
          <div v-else-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
              <ion-row class="table-header">
                <ion-col size="2"><strong>Archivo</strong></ion-col>
                <ion-col size="1.5"><strong>Estado</strong></ion-col>
                <ion-col size="1.5"><strong>Trigger</strong></ion-col>
                <ion-col size="2"><strong>Ejecutado por</strong></ion-col>
                <ion-col size="1"><strong>Tamaño</strong></ion-col>
                <ion-col size="1"><strong>Duración</strong></ion-col>
                <ion-col size="2"><strong>Creado</strong></ion-col>
                <ion-col size="1"><strong>Acciones</strong></ion-col>
              </ion-row>
              <ion-row v-if="loading && !polling" class="row-loading">
                <ion-col class="row-loading-col">
                  <ion-spinner name="crescent"></ion-spinner>
                  <span>Cargando...</span>
                </ion-col>
              </ion-row>
              <template v-else>
                <ion-row v-for="backup in paginatedItems" :key="backup.id" class="log-row" @click="openDetail(backup)">
                  <ion-col size="2" class="cell-truncate">{{ backup.filename }}</ion-col>
                  <ion-col size="1.5">
                    <ion-chip :color="statusColor(backup.status)" size="small" class="action-chip">{{ formatStatus(backup.status) }}</ion-chip>
                  </ion-col>
                  <ion-col size="1.5">{{ formatTrigger(backup.trigger_type) }}</ion-col>
                  <ion-col size="2" class="cell-truncate">{{ backup.triggered_by?.username || 'CLI / Automático' }}</ion-col>
                  <ion-col size="1">{{ backup.size_formatted || formatBytes(backup.size_bytes) }}</ion-col>
                  <ion-col size="1">{{ formatDuration(backup.duration_seconds) }}</ion-col>
                  <ion-col size="2">{{ formatTimestamp(backup.created_at) }}</ion-col>
                  <ion-col size="1" @click.stop>
                    <QuickActions
                      :to-view="true"
                      @view-clicked="openDetail(backup)"
                    />
                  </ion-col>
                </ion-row>
              </template>
            </ion-grid>
            <div class="pagination">
              <span class="page-size">
                <span class="page-size-label">Filas:</span>
                <select :value="itemsPerPage" class="items-per-page-select" @change="setPageSize(Number($event.target.value))">
                  <option :value="10">10</option>
                  <option :value="20">20</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </span>
              <ion-button fill="clear" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
                <ion-icon :icon="icons.chevronBack" slot="icon-only"></ion-icon>
              </ion-button>
              <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
              <ion-button fill="clear" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
                <ion-icon :icon="icons.chevronForward" slot="icon-only"></ion-icon>
              </ion-button>
            </div>
          </div>
          <!-- Mobile -->
          <div v-else class="mobile-list">
            <div v-if="loading && !polling" class="mobile-loading">
              <ion-spinner name="crescent"></ion-spinner><span>Cargando...</span>
            </div>
            <template v-else>
              <div v-for="backup in paginatedItems" :key="backup.id" class="mobile-card" @click="openDetail(backup)">
                <div class="mobile-card-header">
                  <ion-chip :color="statusColor(backup.status)" size="small" class="action-chip">{{ formatStatus(backup.status) }}</ion-chip>
                  <span class="mobile-timestamp">{{ formatTimestamp(backup.created_at) }}</span>
                </div>
                <div class="mobile-card-body">
                  <strong>{{ backup.filename }}</strong>
                  <span class="mobile-meta">{{ formatTrigger(backup.trigger_type) }} · {{ backup.size_formatted || formatBytes(backup.size_bytes) }}</span>
                  <span class="mobile-meta">{{ backup.triggered_by?.username || 'CLI / Automático' }} · {{ formatDuration(backup.duration_seconds) }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Filters modal -->
    <ion-modal :is-open="isFiltersModalOpen" @did-dismiss="closeFiltersModal" class="filters-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Filtros</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeFiltersModal"><ion-icon :icon="icons.close"></ion-icon></ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <div class="filters-modal-content">
        <label class="filter-field full">
          <span>Estado</span>
          <ion-select v-model="statusFilter" placeholder="Seleccionar estado" @ionChange="triggerFetch">
            <ion-select-option value="">Todos</ion-select-option>
            <ion-select-option value="PENDING">Pendiente</ion-select-option>
            <ion-select-option value="IN_PROGRESS">En progreso</ion-select-option>
            <ion-select-option value="COMPLETED">Completado</ion-select-option>
            <ion-select-option value="FAILED">Fallido</ion-select-option>
          </ion-select>
        </label>
        <label class="filter-field full">
          <span>Tipo de trigger</span>
          <ion-select v-model="triggerTypeFilter" placeholder="Seleccionar trigger" @ionChange="triggerFetch">
            <ion-select-option value="">Todos</ion-select-option>
            <ion-select-option value="MANUAL_CLI">Manual (CLI)</ion-select-option>
            <ion-select-option value="MANUAL_API">Manual (API)</ion-select-option>
          </ion-select>
        </label>
        <label class="filter-field full">
          <span>Ordenar</span>
          <ion-select v-model="orderingFilter" placeholder="Ordenar por" @ionChange="triggerFetch">
            <ion-select-option value="-created_at">Recientes primero</ion-select-option>
            <ion-select-option value="created_at">Antiguos primero</ion-select-option>
            <ion-select-option value="-size_bytes">Mayor tamaño</ion-select-option>
            <ion-select-option value="size_bytes">Menor tamaño</ion-select-option>
          </ion-select>
        </label>
      </div>
    </ion-modal>

    <!-- Detail -->
    <ion-modal :is-open="selectedBackup !== null" @did-dismiss="closeDetail" class="detail-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Detalle de backup</ion-title>
          <ion-buttons slot="end"><ion-button @click="closeDetail"><ion-icon :icon="icons.close"></ion-icon></ion-button></ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <template v-if="selectedBackup">
          <ion-card class="info-card">
            <ion-card-header><ion-card-title class="section-title">General</ion-card-title></ion-card-header>
            <ion-card-content>
              <div class="field"><span class="label">ID</span><span class="value">{{ selectedBackup.id }}</span></div>
              <div class="field"><span class="label">Archivo</span><span class="value">{{ selectedBackup.filename }}</span></div>
              <div class="field"><span class="label">Estado</span><span class="value"><ion-chip :color="statusColor(selectedBackup.status)">{{ formatStatus(selectedBackup.status) }}</ion-chip></span></div>
              <div class="field"><span class="label">Trigger</span><span class="value">{{ formatTrigger(selectedBackup.trigger_type) }}</span></div>
              <div class="field"><span class="label">Ejecutado por</span><span class="value">{{ selectedBackup.triggered_by?.username || 'CLI / Automático' }}</span></div>
              <div class="field"><span class="label">Tamaño</span><span class="value">{{ selectedBackup.size_formatted || formatBytes(selectedBackup.size_bytes) }} ({{ selectedBackup.size_bytes }} bytes)</span></div>
              <div class="field"><span class="label">Duración</span><span class="value">{{ formatDuration(selectedBackup.duration_seconds) }}</span></div>
              <div class="field"><span class="label">Creado</span><span class="value">{{ formatTimestamp(selectedBackup.created_at) }}</span></div>
              <div class="field"><span class="label">Completado</span><span class="value">{{ formatTimestamp(selectedBackup.completed_at) }}</span></div>
              <div class="field"><span class="label">Actualizado</span><span class="value">{{ formatTimestamp(selectedBackup.updated_at) }}</span></div>
            </ion-card-content>
          </ion-card>
          <ion-card class="info-card">
            <ion-card-header><ion-card-title class="section-title">Integridad / R2</ion-card-title></ion-card-header>
            <ion-card-content>
              <div class="field"><span class="label">s3_key</span><span class="value">{{ selectedBackup.s3_key }}</span></div>
              <div class="field"><span class="label">SHA256</span><span class="value" style="word-break: break-all">{{ selectedBackup.checksum_sha256 || '-' }}</span></div>
            </ion-card-content>
          </ion-card>
          <ion-card class="info-card" v-if="selectedBackup.notes">
            <ion-card-header><ion-card-title class="section-title">Notas</ion-card-title></ion-card-header>
            <ion-card-content><pre class="json-block">{{ selectedBackup.notes }}</pre></ion-card-content>
          </ion-card>
          <ion-card class="info-card" v-if="selectedBackup.error_message">
            <ion-card-header><ion-card-title class="section-title">Error</ion-card-title></ion-card-header>
            <ion-card-content><pre class="json-block">{{ selectedBackup.error_message }}</pre></ion-card-content>
          </ion-card>
          <div class="action-row">
            <ion-button v-if="selectedBackup.status === 'COMPLETED'" @click="downloadBackup(selectedBackup)" fill="solid" color="success"><ion-icon :icon="icons.cloudDownload" slot="start"></ion-icon>Descargar (URL pre-firmada)</ion-button>
            <ion-button @click="confirmDelete(selectedBackup)" fill="outline" color="danger"><ion-icon :icon="icons.delete" slot="start"></ion-icon>Eliminar</ion-button>
          </div>
        </template>
      </ion-content>
    </ion-modal>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons
      entity-type="backup"
      show-filter
      :show-clear="hasFilters"
      @refresh="fetchBackups"
      @clear="clearFilters"
      @filter="openFiltersModal"
      @itemCreated="fetchBackups"
    />

  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import { toastController, alertController, IonContent, IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent, IonButton, IonIcon, IonChip, IonGrid, IonRow, IonCol, IonSpinner, IonSelect, IonSelectOption, IonTextarea, IonItem, IonLabel, IonHeader, IonToolbar, IonTitle, IonButtons, IonModal } from '@ionic/vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { useServerPagination } from '@composables/Tables/useServerPagination.js'
import QuickControl from '@components/operators/quickControl.vue'
import QuickActions from '@components/operators/quickActions.vue'
import FloatingActionButtons from '@components/operators/FloatingActionButtons.vue'

const authStore = useAuthStore()
const icons = inject('icons', {})
const { isMobile } = useResponsiveView(768)

const backups = ref([])
const loading = ref(true)
const error = ref(null)
const selectedBackup = ref(null)
const isFiltersModalOpen = ref(false)
const polling = ref(false)

const statusFilter = ref('')
const triggerTypeFilter = ref('')
const orderingFilter = ref('-created_at')

const hasFilters = computed(() =>
  statusFilter.value !== '' || triggerTypeFilter.value !== ''
)

let pollTimer = null

const paginatedItems = computed(() => backups.value || [])

const endpoint = API.BACKUPS

const STATUS_LABELS = {
  PENDING: 'Pendiente',
  IN_PROGRESS: 'En progreso',
  COMPLETED: 'Completado',
  FAILED: 'Fallido'
}

const TRIGGER_LABELS = {
  MANUAL_CLI: 'Manual (CLI)',
  MANUAL_API: 'Manual (API)',
  AUTOMATED_SCHEDULE: 'Automático (Programado)',
  SCHEDULED_CELERY: 'Programado (Celery)'
}

const formatStatus = (status) => STATUS_LABELS[status] || status || '-'
const formatTrigger = (trigger) => TRIGGER_LABELS[trigger] || trigger || '-'

const formatTimestamp = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

const formatDuration = (s) => {
  if (s === null || s === undefined) return '-'
  const num = Number(s)
  if (Number.isNaN(num)) return s
  return `${num.toFixed(2)}s`
}

const formatBytes = (b) => {
  if (b === null || b === undefined) return '-'
  const num = Number(b)
  if (Number.isNaN(num)) return b
  const k = 1024
  const units = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(num)/Math.log(k))
  return `${(num/Math.pow(k,i)).toFixed(2)} ${units[i]||''}`
}

const statusColor = (status) => {
  if (status === 'COMPLETED') return 'success'
  if (status === 'FAILED') return 'danger'
  if (status === 'IN_PROGRESS') return 'primary'
  if (status === 'PENDING') return 'warning'
  return 'medium'
}

const buildQuery = () => {
  const params = new URLSearchParams()
  if (statusFilter.value) params.set('status', statusFilter.value)
  if (triggerTypeFilter.value) params.set('trigger_type', triggerTypeFilter.value)
  if (orderingFilter.value) params.set('ordering', orderingFilter.value)
  params.set('page', currentPage.value)
  params.set('page_size', itemsPerPage.value)
  return params.toString()
}

const fetchBackups = async (silent = false) => {
  if (!authStore.isSuperUser) {
    error.value = 'Solo superusuarios pueden acceder a backups'
    loading.value = false
    return
  }
  if (!silent) {
    loading.value = true
    error.value = null
  }
  try {
    const qs = buildQuery()
    const url = qs ? `${endpoint}?${qs}` : endpoint
    const response = await API.get(url)
    const payload = Array.isArray(response) ? response[0] : response
    backups.value = payload?.results ?? []
    setTotal(payload?.count)
    // start/stop polling if any IN_PROGRESS
    const hasInProgress = backups.value.some(b => b.status === 'IN_PROGRESS')
    startPolling(hasInProgress)
  } catch (err) {
    error.value = err.message || 'Error al cargar backups'
    backups.value = []
  } finally {
    if (!silent) loading.value = false
  }
}

const startPolling = (shouldPoll) => {
  if (shouldPoll && !pollTimer) {
    pollTimer = setInterval(() => {
      polling.value = true
      fetchBackups(true).finally(() => { polling.value = false })
    }, 5000)
  } else if (!shouldPoll && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
    polling.value = false
  }
}

onMounted(() => {
  fetchBackups()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const { currentPage, itemsPerPage, totalPages, setTotal, changePage, setPageSize, resetToFirstPage } = useServerPagination({ fetchFn: fetchBackups, pageSize: 20 })

const triggerFetch = () => {
  resetToFirstPage()
  fetchBackups()
}

const clearFilters = () => {
  statusFilter.value = ''
  triggerTypeFilter.value = ''
  orderingFilter.value = '-created_at'
  resetToFirstPage()
  fetchBackups()
}

const openDetail = async (backup) => {
  try {
    const resp = await API.get(API.BACKUP_DETAIL(backup.id))
    const payload = Array.isArray(resp) ? resp[0] : resp
    selectedBackup.value = payload
  } catch (err) {
    const toast = await toastController.create({ message: err.message || 'Error al cargar detalle', duration: 3000, color: 'danger', position: 'bottom' })
    toast.present()
  }
}

const closeDetail = () => { selectedBackup.value = null }

const openFiltersModal = () => { isFiltersModalOpen.value = true }
const closeFiltersModal = () => { isFiltersModalOpen.value = false }

const triggerBrowserDownload = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const downloadBackup = async (backup) => {
  try {
    const resp = await API.post(API.BACKUP_DOWNLOAD_URL(backup.id), {})
    const payload = Array.isArray(resp) ? resp[0] : resp
    const downloadUrl = payload.download_url
    if (!downloadUrl) throw new Error('URL no disponible')

    const filename = payload.filename || backup.filename || 'backup.dump'

    if (/^https?:\/\//.test(downloadUrl)) {
      window.open(downloadUrl, '_blank')
    } else {
      // Vía local (cloud storage no configurada): traer con auth como blob
      const endpoint = downloadUrl.replace(/^\/api\/v1\//, '')
      const blob = await API.get(endpoint, {}, { responseType: 'blob' })
      triggerBrowserDownload(blob, filename)
    }
    const toast = await toastController.create({ message: 'Descarga iniciada', duration: 2500, color: 'success', position: 'bottom' })
    toast.present()
  } catch (err) {
    const toast = await toastController.create({ message: err.message || 'Error al generar URL', duration: 3000, color: 'danger', position: 'bottom' })
    toast.present()
  }
}

const confirmDelete = async (backup) => {
  const alert = await alertController.create({
    header: 'Confirmar eliminación',
    message: `¿Eliminar el backup "${backup.filename}"? Esto no se puede deshacer.`,
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      { text: 'Eliminar', role: 'destructive', handler: () => deleteBackup(backup) }
    ]
  })
  await alert.present()
}

const deleteBackup = async (backup) => {
  try {
    await API.delete(API.BACKUP_DETAIL(backup.id))
    const toast = await toastController.create({ message: 'Backup eliminado', duration: 2000, color: 'success', position: 'bottom' })
    toast.present()
    closeDetail()
    await fetchBackups()
  } catch (err) {
    const toast = await toastController.create({ message: err.message || 'Error al eliminar backup', duration: 3000, color: 'danger', position: 'bottom' })
    toast.present()
  }
}

defineExpose({ fetchBackups })
</script>

<style scoped>
.table-card {
  margin: 0 auto;
}

ion-card-header {
  padding-bottom: 8px;
}

ion-card-subtitle {
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

.filter-field span {
  font-size: 0.72rem;
  color: var(--ion-color-medium);
  padding-left: 4px;
}

.filter-select,
.filter-input {
  height: 56px;
  box-sizing: border-box;
  min-width: 150px;
  max-width: 220px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  background: var(--ion-card-background, #fff);
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

.filter-field.full ion-select,
.filter-field.full ion-input {
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

.filter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.filter-actions ion-button {
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
  font-weight: 600;
}

.table-header ion-col,
.log-row ion-col {
  display: flex;
  align-items: center;
  min-height: 48px;
  padding: 8px 12px;
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

.detail-modal {
  --width: 680px;
  --height: 85vh;
  --max-height: 90vh;
}

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

.field {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--ion-color-light-shade, #e5e7eb);
  gap: 16px;
  flex-wrap: wrap;
}

.label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ion-color-medium);
  letter-spacing: 0.4px;
  text-transform: uppercase;
  min-width: 120px;
}

.value {
  font-size: 1rem;
  color: var(--ion-color-dark);
  flex: 1;
  text-align: right;
  word-break: break-word;
  line-height: 1.5;
}

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

.action-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .table-card {
    margin: 0 auto;
  }

  .pagination {
    flex-wrap: wrap;
  }

  .info-card {
    margin: 12px 0;
  }
}
</style>