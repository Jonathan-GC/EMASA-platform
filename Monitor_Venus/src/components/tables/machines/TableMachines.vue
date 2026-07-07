<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Máquinas de los clientes registradas</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${machines.length} ${machines.length === 1 ? 'máquina encontrada' : 'máquinas encontradas'} ` }}
        </ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de máquinas...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchmáquinas" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="machines.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar 
              v-model="searchText"
              placeholder="Buscar máquina..."
              @ionInput="handleSearch"
              show-clear-button="focus"
              class="custom"
            ></ion-searchbar>
            
            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchmáquinas" fill="clear">
                <ion-icon :icon="icons.refresh"></ion-icon>
              </ion-button>
              <QuickControl
                  :toCreate="true"
                  type="machine"
                  @itemCreated="handleItemRefresh"
              />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <div v-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
            <!-- Header -->
            <ion-row class="table-header">
              <ion-col size="2" @click="sortBy('name')" class="sortable">
                <strong>Nombre</strong>
                <ion-icon
                  :icon="sortOrder.name === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('id')" class="sortable">
                <strong>ID</strong>
                <ion-icon 
                  :icon="sortOrder.id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'id'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('tenant')" class="sortable">
                <strong>Tenant</strong>
                <ion-icon 
                  :icon="sortOrder.tenant === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'tenant'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>Workspace</strong>
              </ion-col>

              <ion-col size="1">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row 
              v-for="machine in paginatedItems" 
              :key="machine.id"
              class="table-row-stylized"
             
              :class="{ 'row-selected': selectedmachine?.id === machine.id }"
            >
              <ion-col size="2">
                <div class="machine-info">
                  <ion-icon 
                    :icon="icons.hardwareChip" 
                    :color="getStatusColor(machine.state)"
                  ></ion-icon>
                  <div>
                    <div>{{ machine.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div>{{ machine.id }}</div>
              </ion-col>

              <ion-col size="2">
                <ion-chip>
                  {{ machine.workspace.tenant }}
                </ion-chip>
              </ion-col>
              
              <ion-col size="2">
                <div class="location-info">
                  <ion-icon :icon="icons.location" size="small"></ion-icon>
                  {{ machine.workspace.name }}
                </div>
              </ion-col>
              
              
              <ion-col size="1">
                <quick-actions 
                  type="machine"
                  :index="machine.id" 
                  :name="machine.name"
                  :to-view="true"
                  to-edit
                  to-delete
                  :initial-data="setInitialData(machine)"
                  @item-edited="handleItemRefresh"
                  @item-deleted="handleItemRefresh"
                  @view-clicked="openMachineModal(machine.id)"
                />
              </ion-col>
            </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card v-for="machine in paginatedItems" :key="machine.id" class="machine-card">
              <ion-card-content>
                <!-- Header with icon and name -->
                <div class="card-header">
                  <div class="card-icon-title">
                    <ion-icon 
                      :icon="icons.hardwareChip" 
                      :color="getStatusColor(machine.state)"
                      class="card-icon-large"
                    ></ion-icon>
                    <div class="card-title-section">
                      <h3 class="card-title">{{ machine.name }}</h3>
                      <p class="card-subtitle">ID: {{ machine.id }}</p>
                    </div>
                  </div>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Tenant:</span>
                    <span class="detail-value">
                      <ion-chip size="small">{{ machine.workspace.tenant }}</ion-chip>
                    </span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">
                      <ion-icon :icon="icons.location" size="small"></ion-icon>
                      Workspace:
                    </span>
                    <span class="detail-value">{{ machine.workspace.name }}</span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <quick-actions 
                    type="machine"
                    :index="machine.id" 
                    :name="machine.name"
                    :to-view="true"
                    to-edit
                    to-delete
                    :initial-data="setInitialData(machine)"
                    @item-edited="handleItemRefresh"
                    @item-deleted="handleItemRefresh"
                    @view-clicked="openMachineModal(machine.id)"
                  />
                </div>
              </ion-card-content>
            </ion-card>
          </div>

          <!-- Pagination -->
          <div class="pagination" v-if="totalPages > 1">
            <ion-button 
              fill="clear" 
              :disabled="currentPage === 1"
              @click="changePage(currentPage - 1)"
            >
              <ion-icon :icon="icons.chevronBack"></ion-icon>
            </ion-button>
            
            <span class="page-info">
              Página {{ currentPage }} de {{ totalPages }}
            </span>
            
            <ion-button 
              fill="clear" 
              :disabled="currentPage === totalPages"
              @click="changePage(currentPage + 1)"
            >
              <ion-icon :icon="icons.chevronForward"></ion-icon>
            </ion-button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <ion-icon :icon="icons.server" size="large" color="medium"></ion-icon>
          <h3>No hay máquinas</h3>
          <p>No se encontraron máquinas en el sistema</p>
          <QuickControl :toCreate="true" type="machine" @itemCreated="handleItemRefresh" />
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="machine"
      @refresh="fetchmáquinas"
      @itemCreated="handleItemRefresh"
    />

    <!-- Machine Details Modal -->
    <ion-modal :is-open="isModalOpen" @did-dismiss="closeModal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Detalles de la Máquina</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <!-- Loading state -->
        <div v-if="loadingDetails" class="modal-loading">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Cargando detalles...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="detailsError" class="modal-error">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>{{ detailsError }}</p>
        </div>

        <!-- Machine details -->
        <div v-else-if="selectedMachineDetails" class="machine-details">
          <!-- Machine Header with Image -->
          <div class="machine-header">
            <div class="machine-header-left">
              <div class="machine-icon-wrapper">
                <ion-icon :icon="icons.hardwareChip" color="white"></ion-icon>
              </div>
              <div class="machine-title-section">
                <h2 class="machine-name">{{ selectedMachineDetails.name }}</h2>
                <p class="machine-id">ID: {{ selectedMachineDetails.id }}</p>
              </div>
            </div>
            <div v-if="selectedMachineDetails.img" class="machine-image-wrapper">
              <img :src="selectedMachineDetails.img" alt="Machine image" class="machine-image" />
            </div>
          </div>

          <!-- Machine Information -->
          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.info" color="primary"></ion-icon>
                Información General
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <div class="info-grid">
                <div class="info-item full-width">
                  <label class="info-label">Descripción</label>
                  <p class="info-value">{{ selectedMachineDetails.description || 'Sin descripción' }}</p>
                </div>
              </div>
            </ion-card-content>
          </ion-card>

          <!-- Workspace Information -->
          <ion-card class="info-card">
            <ion-card-header>
              <ion-card-title class="section-title">
                <ion-icon :icon="icons.business" color="primary"></ion-icon>
                Información del Workspace
              </ion-card-title>
            </ion-card-header>
            <ion-card-content>
              <div class="info-grid">
                <div class="info-item">
                  <label class="info-label">Workspace</label>
                  <p class="info-value">
                    <ion-chip color="primary">
                      <ion-label>{{ selectedMachineDetails.workspace?.name || 'N/A' }}</ion-label>
                    </ion-chip>
                  </p>
                </div>
                
                <div class="info-item">
                  <label class="info-label">Tenant</label>
                  <p class="info-value">
                    <ion-chip color="primary">
                      <ion-label>{{ selectedMachineDetails.workspace?.tenant || 'N/A' }}</ion-label>
                    </ion-chip>
                  </p>
                </div>

                <div class="info-item">
                  <label class="info-label">Workspace ID</label>
                  <p class="info-value info-mono">{{ selectedMachineDetails.workspace?.id || 'N/A' }}</p>
                </div>

                <div class="info-item">
                  <label class="info-label">Tenant ID</label>
                  <p class="info-value info-mono">{{ selectedMachineDetails.workspace?.tenant_id || 'N/A' }}</p>
                </div>
              </div>
            </ion-card-content>
          </ion-card>
        </div>

        <!-- Fallback if no data -->
        <div v-else class="modal-empty">
          <p>No hay datos disponibles</p>
        </div>
      </ion-content>
    </ion-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, inject } from 'vue'
import API from '@utils/api/api'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useTableSorting } from '@composables/Tables/useTableSorting.js'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { formatTime, getStatusColor } from '@utils/formatters/formatters'
import QuickControl from '../../operators/quickControl.vue'
import FloatingActionButtons from '../../operators/FloatingActionButtons.vue'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Responsive view detection
const { isMobile, isTablet, isDesktop } = useResponsiveView(768)

// Component-specific state
const machines = ref([])
const loading = ref(false)
const error = ref(null)
const selectedmachine = ref(null)
const isMounted = ref(false)

// Modal state
const isModalOpen = ref(false)
const selectedMachineDetails = ref(null)
const loadingDetails = ref(false)
const detailsError = ref(null)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(machines, ['name', 'id', 'workspace.tenant', 'workspace.name'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'

const setInitialData = (item) => {
  return {
    name: item.name,
    description: item.description,
    workspace_id: item.workspace.id
  }
}

// Fetch data from API
const fetchMachines = async () => {
  // Ensure component is mounted before fetching
  if (!isMounted.value) {
    console.log('⏳ Component not ready, waiting...')
    return
  }
  
  loading.value = true
  error.value = null
  const headers={
    //Authorization: `Bearer ${localStorage.getItem('token')}`
  }
  
  try {
    console.log('🔄 Fetching máquinas data...')
    
    // Real API call using await
    const response = await API.get(API.MACHINE, headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);
    
    machines.value = mockData
    console.log('✅ máquinas cargados:', mockData.length)
    
  } catch (err) {
    error.value = `❌Error al cargar máquinas: ${err.message}`
    console.error('❌ Error fetching máquinas:', err)
  } finally {
    loading.value = false
  }
}

// Component-specific methods
const selectmachine = (machine) => {
  selectedmachine.value = machine
  console.log('machine seleccionado:', machine)
}

const viewmachine = (machine) => {
  console.log('Ver detalles del machine:', machine)
  // Aquí podrías navegar a una página de detalles
  // router.push(`/máquinas/${machine.id}`)
}

const handleItemRefresh = () => {
  fetchMachines();
};

// Modal functions
const openMachineModal = async (machineId) => {
  console.log('🔍 Opening modal for machine ID:', machineId)
  isModalOpen.value = true
  loadingDetails.value = true
  detailsError.value = null
  selectedMachineDetails.value = null
  
  const headers = {
    // Authorization: `Bearer ${localStorage.getItem('token')}`
  }
  
  try {
    console.log('🔄 Fetching machine details for ID:', machineId)
    console.log('📍 API endpoint:', `${API.MACHINE}${machineId}/`)
    const response = await API.get(`${API.MACHINE}${machineId}/`, headers)
    console.log('✅ Machine details loaded:', response)
    console.log('📊 Response type:', typeof response, 'Is array:', Array.isArray(response))
    
    // Handle if response is wrapped in a data property, is an array, or is the object directly
    let data = response?.data || response
    // If the response is an array, take the first element
    if (Array.isArray(data) && data.length > 0) {
      data = data[0]
    }
    selectedMachineDetails.value = data
    console.log('💾 selectedMachineDetails set to:', selectedMachineDetails.value)
  } catch (err) {
    detailsError.value = `Error al cargar detalles: ${err.message}`
    console.error('❌ Error fetching machine details:', err)
  } finally {
    loadingDetails.value = false
    console.log('⏹️ Loading finished. Modal open:', isModalOpen.value, 'Has data:', !!selectedMachineDetails.value)
  }
}

const closeModal = () => {
  isModalOpen.value = false
  selectedMachineDetails.value = null
  detailsError.value = null
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 Tablemáquinas component mounted')
  
  // Wait for next tick to ensure DOM is ready
  await nextTick()
  
  // Mark component as mounted
  isMounted.value = true
  
  // Small delay to ensure Ionic page transition is complete
  setTimeout(() => {
    fetchMachines()
  }, 100)
})
</script>

















<style scoped>

.loading-container, .error-container, .empty-state {
  text-align: center;
  padding: 40px 20px;
}

.loading-container ion-spinner {
  margin-bottom: 16px;
}

.error-container ion-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.desktop-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--ion-color-light);
  border-radius: 8px;
}

.data-table {
  min-width: 1000px;
  margin: 0;
}


.table-header ion-col {
  padding: 16px 12px;
}

.sortable {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.sortable:hover {
  background-color: var(--ion-color-light-tint);
}

.table-row-stylized {
  border-bottom: 1px solid var(--ion-color-light);
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.table-row-stylized:hover {
  background-color: var(--ion-color-light-tint);
}

.row-selected {
  background-color: var(--ion-color-primary-tint) !important;
}

.table-row-stylized ion-col {
  padding: 12px;
  display: flex;
  align-items: center;
}

.machine-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.machine-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.machine-id {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.location-info, .time-info, .devices-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 16px;
}

.page-info {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .table-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .data-table {
    font-size: 0.8rem;
  }

  .table-header ion-col,
  .table-row-stylized ion-col {
    padding: 8px 6px;
  }

  .machine-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Mobile Cards Styles */
.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.machine-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.machine-card ion-card-content {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ion-color-light);
}

.card-icon-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.card-icon-large {
  font-size: 32px;
  flex-shrink: 0;
}

.card-title-section {
  flex: 1;
  min-width: 0;
}

.card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-subtitle {
  margin: 4px 0 0 0;
  font-size: 0.85rem;
  color: var(--ion-color-medium);
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.card-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.detail-label {
  color: var(--ion-color-medium);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.detail-value {
  color: var(--ion-color-dark);
  display: flex;
  align-items: center;
  gap: 4px;
}

.detail-value ion-chip {
  margin: 0;
  height: 22px;
  font-size: 0.8rem;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}

/* Modal Styles */
.modal-loading,
.modal-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.modal-loading ion-spinner {
  margin-bottom: 16px;
}

.modal-error ion-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.machine-details {
  padding: 0;
}

/* Machine Header */
.machine-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  background: linear-gradient(135deg, var(--ion-color-primary-tint) 0%, var(--ion-color-primary) 100%);
  color: white;
  gap: 20px;
}

.machine-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.machine-icon-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.machine-icon-wrapper ion-icon {
  font-size: 32px;
  color: white;
}

.machine-title-section {
  flex: 1;
}

.machine-name {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
  line-height: 1.3;
}

.machine-id {
  margin: 6px 0 0 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.9);
  font-family: 'Courier New', monospace;
}

.machine-image-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.machine-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Info Cards */
.info-card {
  margin: 16px;
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
  font-size: 1.1rem;
  font-weight: 600;
}

.section-title ion-icon {
  font-size: 24px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ion-color-medium);
  letter-spacing: 0.5px;
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

.modal-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

/* Responsive */
@media (min-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .machine-image-wrapper {
    width: 140px;
    height: 140px;
  }
}

@media (max-width: 576px) {
  .machine-header {
    flex-direction: column;
  }
  
  .machine-image-wrapper {
    width: 100%;
    height: 200px;
  }
}
</style>
