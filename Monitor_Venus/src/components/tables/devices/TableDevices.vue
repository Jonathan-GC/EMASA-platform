<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>📟 Devices - Datos desde API</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${application.length} applications encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de los Applications...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchApplications" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="application.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar
                v-model="searchText"
                placeholder="Buscar device profile..."
                @ionInput="handleSearch"
                show-clear-button="focus"
            ></ion-searchbar>

            <ion-button @click="fetchApplications" fill="clear">
              <ion-icon :icon="icons.refresh"></ion-icon>
            </ion-button>

            <QuickControl
                :toCreate="true"
                type="application"
                @itemCreated="handleItemRefresh"
            />
          </div>

          <!-- Table using ion-grid -->
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
              <ion-col size="2" @click="sortBy('lastSeen')" class="sortable">
                <strong>Cliente</strong>
                <ion-icon
                    :icon="sortOrder.lastSeen === 'asc' ? icons.chevronUp : icons.chevronDown"
                    v-if="sortField === 'lastSeen'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>Tipo</strong>
              </ion-col>
              <ion-col size="1">
                <strong>Dispositivos</strong>
              </ion-col>
              <ion-col size="2" @click="sortBy('status')" class="sortable">
                <strong>Estado de sincronización</strong>
                <ion-icon
                    :icon="sortOrder.status === 'asc' ? icons.chevronUp : icons.chevronDown"
                    v-if="sortField === 'status'"
                ></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>


            <!-- Data rows -->
            <ion-row
                v-for="deviceProfile in paginatedItems"
                :key="deviceProfile.id"
                class="table-row-stylized"

                :class="{ 'row-selected': selectedApplication?.id === deviceProfile.id }"
            >
              <ion-col size="2">
                <div class="gateway-info">
                  <div>
                    <div class="gateway-name">{{ deviceProfile.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="gateway-id">{{ deviceProfile.cs_application_id }}</div>
              </ion-col>


              <ion-col size="2">
                <ion-chip class="p-2.5 rounded-full">
                  {{ deviceProfile.workspace.tenant }}
                </ion-chip>
              </ion-col>

              <ion-col size="2">
                <div class="location-info">
                  <ion-icon :icon="icons.globe" size="small"></ion-icon>
                  {{ deviceProfile.device_type }}
                </div>
              </ion-col>

              <ion-col size="1">
                <div class="devices-info">
                  <ion-icon :icon="icons.phonePortrait" size="small"></ion-icon>
                  {{ deviceProfile.connectedDevices || 0 }}
                </div>
              </ion-col>
              <ion-col size="2">
                <ion-chip
                    :color="getStatusColor(deviceProfile.sync_status)"
                >
                  {{ deviceProfile.sync_status }}
                </ion-chip>
              </ion-col>

              <ion-col size="1">
                <ion-button
                    fill="clear"
                    size="small"
                    @click="router.push(`devices/${deviceProfile.id}`)"
                >
                  <ion-icon :icon="icons.eye"></ion-icon>

                  
                </ion-button>
              </ion-col>
            </ion-row>
          </ion-grid>

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
          <h3>No hay gateways</h3>
          <p>No se encontraron gateways en el sistema</p>
          <ion-button @click="fetchApplications" fill="outline">
            Buscar gateways
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import API from '@utils/api/api'
import { parameters } from '@/plugins/router/parameters.js'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useTableSorting } from '@composables/Tables/useTableSorting.js'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { formatTime, getStatusColor } from '@utils/formatters/formatters'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})
const router = useRouter()
const route = useRoute()

// Component-specific state
const application = ref([])
const loading = ref(false)
const error = ref(null)
const selectedApplication = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(application, ['name', 'cs_gateway_id', 'location'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'



// Fetch data from API
const fetchApplications = async () => {
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
    console.log('🔄 Fetching Application data...')

    // Real API call using await
    const response = await API.get(API.APPLICATION_DEVICES(route.params.application_id), headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);

    application.value = mockData
    console.log('✅ Gateways cargados:', mockData.length)

  } catch (err) {
    error.value = `❌Error al cargar gateways: ${err.message}`
    console.error('❌ Error fetching Application:', err)
  } finally {
    loading.value = false
  }
}

// Component-specific methods
const selectGateway = (gateway) => {
  selectedApplication.value = gateway
  console.log('Gateway seleccionado:', gateway)
}

const viewGateway = (gateway) => {
  console.log('Ver detalles del gateway:', gateway)
  // Aquí podrías navegar a una página de detalles
  // router.push(`/Application/${gateway.id}`)
}

const handleItemRefresh = () => {
  fetchApplications();
};

// Lifecycle
onMounted(async () => {
  console.log('🔧 TableGateways component mounted')

  // Wait for next tick to ensure DOM is ready
  await nextTick()

  // Mark component as mounted
  isMounted.value = true

  // Small delay to ensure Ionic page transition is complete
  setTimeout(() => {
    fetchApplications()
  }, 100)
})
</script>

















<style scoped>

.table-card{
  width: 100%;
  margin: 0 auto;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
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

.data-table {
  border: 1px solid var(--ion-color-light);
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  background-color: var(--ion-color-light);
  border-bottom: 2px solid var(--ion-color-medium);
  font-weight: 600;
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
</style>
