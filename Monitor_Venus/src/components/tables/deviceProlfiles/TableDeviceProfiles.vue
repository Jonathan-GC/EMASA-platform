<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>🌐 Device Profiles - Datos desde API</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${deviceProfile.length} device profiles encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de device profiles...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="GetDeviceProfiles" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="deviceProfile.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar v-model="searchText" placeholder="Buscar device profile..." @ionInput="handleSearch"
              show-clear-button="focus" class="custom"></ion-searchbar>

            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="GetDeviceProfiles" fill="clear">
                <ion-icon :icon="icons.refresh"></ion-icon>
              </ion-button>
              <QuickControl :toCreate="true" type="device_profile" @itemCreated="handleItemRefresh" />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <div v-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
            <!-- Header -->
            <ion-row class="table-header">
              <ion-col size="2" @click="sortBy('name')" class="sortable">
                <strong>Nombre</strong>
                <ion-icon :icon="sortOrder.name === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"></ion-icon>
              </ion-col>
              <ion-col size="3" @click="sortBy('cs_device_profile_id')" class="sortable">
                <strong>ID</strong>
                <ion-icon :icon="sortOrder.cs_deviceProfile_id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'cs_device_profile_id'"></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('region')" class="sortable">
                <strong>Region</strong>
                <ion-icon :icon="sortOrder.region === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'region'"></ion-icon>
              </ion-col>

              <ion-col size="2" @click="sortBy('mac_version')" class="sortable">
                <strong>Version MAC</strong>
                <ion-icon :icon="sortOrder.mac_version === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'mac_version'"></ion-icon>
              </ion-col>
              <ion-col size="1" @click="sortBy('reg_param_revision')" class="sortable">
                <strong>Revision</strong>
                <ion-icon :icon="sortOrder.reg_param_revision === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'reg_param_revision'"></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row v-for="deviceProfile in paginatedItems" :key="deviceProfile.id" class="table-row-stylized"
              :class="{ 'row-selected': selecteddeviceProfile?.id === deviceProfile.id }">
              <ion-col size="2">
                <div class="deviceProfile-info">
                  {{ deviceProfile.name }}
                </div>
              </ion-col>
              <ion-col size="3">
                <div class="deviceProfile-id">{{ deviceProfile.cs_device_profile_id }}</div>
              </ion-col>

              <ion-col size="2">
                <ion-chip :color="getStatusColor(deviceProfile.state)">
                  <ion-icon :icon="icons.globe" size="small mr-1"></ion-icon>
                  {{ deviceProfile.region }}
                </ion-chip>
              </ion-col>

              <ion-col size="2">
                <div class="location-info">
                  {{ formatUnderscoreToSpace(deviceProfile.mac_version) }}
                </div>
              </ion-col>

              <ion-col size="1">
                <div class="time-info">
                  {{ deviceProfile.reg_param_revision }}
                </div>
              </ion-col>

              <ion-col size="1">
                <quick-actions 
                  type="device_profile"
                  :index="deviceProfile.id" 
                  :name="deviceProfile.name"
                  :to-view="`/tenants/${deviceProfile.id}`"
                  to-edit
                  to-delete
                  :initial-data="setInitialData(deviceProfile)"
                  @item-edited="handleItemRefresh"
                  @item-deleted="handleItemRefresh"
                />
              </ion-col>
            </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card v-for="deviceProfile in paginatedItems" :key="deviceProfile.id" class="device-profile-card">
              <ion-card-content>
                <!-- Header with name and region -->
                <div class="card-header">
                  <div class="card-title-section">
                    <h3 class="card-title">{{ deviceProfile.name }}</h3>
                    <p class="card-subtitle">{{ deviceProfile.cs_device_profile_id }}</p>
                  </div>
                  <ion-chip :color="getStatusColor(deviceProfile.state)" class="card-chip-status">
                    <ion-icon :icon="icons.globe" size="small"></ion-icon>
                    {{ deviceProfile.region }}
                  </ion-chip>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Versión MAC:</span>
                    <span class="detail-value">{{ formatUnderscoreToSpace(deviceProfile.mac_version) }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Revisión:</span>
                    <span class="detail-value">{{ deviceProfile.reg_param_revision }}</span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <quick-actions 
                    type="device_profile"
                    :index="deviceProfile.id" 
                    :name="deviceProfile.name"
                    :to-view="`/tenants/${deviceProfile.id}`"
                    to-edit
                    to-delete
                    :initial-data="setInitialData(deviceProfile)"
                    @item-edited="handleItemRefresh"
                    @item-deleted="handleItemRefresh"
                  />
                </div>
              </ion-card-content>
            </ion-card>
          </div>

          <!-- Pagination -->
          <div class="pagination" v-if="totalPages > 1">
            <ion-button fill="clear" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
              <ion-icon :icon="icons.chevronBack"></ion-icon>
            </ion-button>

            <span class="page-info">
              Página {{ currentPage }} de {{ totalPages }}
            </span>

            <ion-button fill="clear" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
              <ion-icon :icon="icons.chevronForward"></ion-icon>
            </ion-button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <ion-icon :icon="icons.server" size="large" color="medium"></ion-icon>
          <h3>No hay device profiles</h3>
          <p>No se encontraron device profiles en el sistema</p>
          <ion-button @click="GetDeviceProfiles" fill="outline">
            Buscar device profiles
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="device_profile"
      @refresh="GetDeviceProfiles"
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
import { formatTime, getStatusColor, formatUnderscoreToSpace } from '@utils/formatters/formatters'
import QuickControl from '../../operators/quickControl.vue'
import FloatingActionButtons from '../../operators/FloatingActionButtons.vue'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Responsive view detection
const { isMobile, isTablet, isDesktop } = useResponsiveView(768)

// Component-specific state
const deviceProfile = ref([])
const loading = ref(false)
const error = ref(null)
const selecteddeviceProfile = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(deviceProfile, ['name', 'cs_device_profile_id', 'region', 'mac_version', 'reg_param_revision'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'



// Fetch data from API
const GetDeviceProfiles = async () => {
  // Ensure component is mounted before fetching
  if (!isMounted.value) {
    console.log('⏳ Component not ready, waiting...')
    return
  }

  loading.value = true
  error.value = null
  const headers = {
    //Authorization: `Bearer ${localStorage.getItem('token')}`
  }

  try {
    console.log('🔄 Fetching device profiles data...')

    // Real API call using await
    const response = await API.get(API.DEVICE_PROFILE, headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);

    deviceProfile.value = mockData
    console.log('✅ deviceProfile cargados:', mockData.length)

  } catch (err) {
    error.value = `❌Error al cargar deviceProfile: ${err.message}`
    console.error('❌ Error fetching deviceProfile:', err)
  } finally {
    loading.value = false
  }
}

const setInitialData = (workspace) => {
  return {
    name: workspace.name,
    description: workspace.description,
    region: workspace.region,
    workspace_id: workspace.workspace?.id,
    abp_rx1_delay: workspace.abp_rx1_delay,
    abp_rx1_dr_offset: workspace.abp_rx1_dr_offset,
    abp_rx2_freq: workspace.abp_rx2_freq,
    abp_rx2_dr: workspace.abp_rx2_dr,
  }
}

const handleItemRefresh = () => {
  GetDeviceProfiles()
}

// Component-specific methods
const selectdeviceProfile = (deviceProfile) => {
  selecteddeviceProfile.value = deviceProfile
  console.log('deviceProfile seleccionado:', deviceProfile)
}

const viewdeviceProfile = (deviceProfile) => {
  console.log('Ver detalles del deviceProfile:', deviceProfile)
  // Aquí podrías navegar a una página de detalles
  // router.push(`/deviceProfile/${deviceProfile.id}`)
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 TabledeviceProfile component mounted')

  // Wait for next tick to ensure DOM is ready
  await nextTick()

  // Mark component as mounted
  isMounted.value = true

  // Small delay to ensure Ionic page transition is complete
  setTimeout(() => {
    GetDeviceProfiles()
  }, 100)
})
</script>

















<style scoped>
.loading-container,
.error-container,
.empty-state {
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

.deviceProfile-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.deviceProfile-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.deviceProfile-id {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.location-info,
.time-info,
.devices-info {
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

  .deviceProfile-info {
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

.device-profile-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.device-profile-card ion-card-content {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.detail-label {
  color: var(--ion-color-medium);
  font-weight: 500;
}

.detail-value {
  color: var(--ion-color-dark);
  text-align: right;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}
</style>
