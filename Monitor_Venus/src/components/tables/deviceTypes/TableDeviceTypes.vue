<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Tipos de nodo del sistema</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${deviceTypes.length} ${deviceTypes.length === 1 ? 'tipo de nodo encontrado' : 'tipos de nodo encontrados'}` }}
        </ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de tipos de nodo...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchDeviceTypes" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="deviceTypes.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar 
              v-model="searchText"
              placeholder="Buscar tipo de nodo..."
              @ionInput="handleSearch"
              show-clear-button="focus"
              class="custom"
            ></ion-searchbar>
            
            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchDeviceTypes" fill="clear" shape="round">
                <ion-icon :icon="icons.refresh" slot="icon-only"></ion-icon>
              </ion-button>
              <QuickControl
                  :toCreate="true"
                  type="device_type"
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
              <ion-col size="2" @click="sortBy('cs_gateway_id')" class="sortable">
                <strong>ID</strong>
                <ion-icon 
                  :icon="sortOrder.cs_gateway_id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'cs_gateway_id'"
                ></ion-icon>
              </ion-col>
              <ion-col size="3" @click="sortBy('description')" class="sortable">
                <strong>Descripción</strong>
                <ion-icon 
                  :icon="sortOrder.description === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'description'"
                ></ion-icon>
              </ion-col> 
              <ion-col size="2">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row 
              v-for="deviceType in paginatedItems" 
              :key="deviceType.id"
              class="table-row-stylized"
             
              :class="{ 'row-selected': selectedGateway?.id === deviceType.id }"
            >
              <ion-col size="2">
                <div class="gateway-info">
                  <ion-icon 
                    :icon="icons.hardwareChip" 
                    :color="getStatusColor(deviceType.state)"
                  ></ion-icon>
                  <div>
                    <div class="gateway-name">{{ deviceType.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="gateway-id">{{ deviceType.id }}</div>
              </ion-col>

              <ion-col size="3">
                <div class="gateway-description">{{ deviceType.description }}</div>
              </ion-col>
              
              <ion-col size="2">
                <QuickActions 
                  type="device_type"
                  :index="deviceType.id" 
                  :name="deviceType.name"
                  to-edit
                  to-delete
                  :initial-data="setInitialData(deviceType)"
                  @item-edited="handleItemRefresh"
                  @item-deleted="handleItemRefresh"
                />
              </ion-col>
            </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card v-for="deviceType in paginatedItems" :key="deviceType.id" class="gateway-card">
              <ion-card-content>
                <!-- Header with icon, name and status -->
                <div class="card-header">
                  <div class="card-icon-title">
                    <ion-icon 
                      :icon="icons.hardwareChip" 
                      :color="getStatusColor(deviceType.state)"
                      class="card-icon-large"
                    ></ion-icon>
                    <div class="card-title-section">
                      <h3 class="card-title">{{ deviceType.name }}</h3>
                      <p class="card-subtitle">ID: {{ deviceType.id }}</p>
                    </div>
                  </div>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">
                      Descripción:
                    </span>
                    <p class="detail-value">{{ deviceType.description|| 'N.A' }}</p>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <QuickActions 
                    type="device_type"
                    :index="deviceType.id" 
                    :name="deviceType.name"
                    to-edit
                    to-delete
                    :initial-data="setInitialData(deviceType)"
                    @item-edited="handleItemRefresh"
                    @item-deleted="handleItemRefresh"
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
          <h3>No hay device types</h3>
          <p>No se encontraron device types en el sistema</p>
          <QuickControl :toCreate="true" type="device_type" @itemCreated="handleItemRefresh" />
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="device_type"
      @refresh="fetchDeviceTypes"
      @itemCreated="handleItemRefresh"
    />
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
const deviceTypes = ref([])
const loading = ref(false)
const error = ref(null)
const selectedGateway = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(deviceTypes, ['name', 'cs_gateway_id', 'location.name', 'state'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'



// Fetch data from API
const fetchDeviceTypes = async () => {
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
    console.log('🔄 Fetching device types data...')
    
    // Real API call using await
    const response = await API.get(API.DEVICE_TYPES, headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);
    
    deviceTypes.value = mockData
    console.log('✅ Gateways cargados:', mockData.length)
    
  } catch (err) {
    error.value = `❌Error al cargar device types: ${err.message}`
    console.error('❌ Error fetching device types:', err)
  } finally {
    loading.value = false
  }
}

const setInitialData = (deviceType) => {
  return {
    name: deviceType.name,
    description: deviceType.description,
  }
}

const handleItemRefresh = () => {
  fetchDeviceTypes()
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 TableDeviceTypes component mounted')
  
  // Wait for next tick to ensure DOM is ready
  await nextTick()
  
  // Mark component as mounted
  isMounted.value = true
  
  // Small delay to ensure Ionic page transition is complete
  setTimeout(() => {  
    fetchDeviceTypes()
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

.gateway-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.gateway-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.gateway-id {
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

  .gateway-info {
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

.gateway-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.gateway-card ion-card-content {
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
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

.card-chip-status {
  flex-shrink: 0;
  height: 24px;
  font-size: 0.75rem;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.card-detail-row {
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
  font-weight: 700;
}

.detail-value {
  color: var(--ion-color-dark);
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}
</style>
