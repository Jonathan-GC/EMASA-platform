<template>
  <div>
    <ion-card>
      <ion-card-header>
        <ion-card-title>🌐 Clientes - Datos desde API</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${tenants.length} tenants encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de los clientes...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchGateways" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="tenants.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar 
              v-model="searchText"
              placeholder="Buscar gateway..."
              @ionInput="handleSearch"
              show-clear-button="focus"
            ></ion-searchbar>
            
            <ion-button @click="fetchGateways" fill="clear">
              <ion-icon :icon="icons.refresh"></ion-icon>
            </ion-button>
            <QuickControl
              :toCreate="true"
              type="tenant"
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
              <ion-col size="2" @click="sortBy('cs_tenant_id')" class="sortable">
                <strong>ID</strong>
                <ion-icon 
                  :icon="sortOrder.cs_tenant_id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'cs_tenant_id'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('status')" class="sortable">
                <strong>Grupo</strong>
                <ion-icon 
                  :icon="sortOrder.status === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'status'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>subscription</strong>
              </ion-col>
              <ion-col size="2" @click="sortBy('lastSeen')" class="sortable">
                <strong>Última conexión</strong>
                <ion-icon 
                  :icon="sortOrder.lastSeen === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'lastSeen'"
                ></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Dispositivos</strong>
              </ion-col>
              <ion-col size="1">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row 
              v-for="gateway in paginatedItems" 
              :key="gateway.id"
              class="table-row-stylized"
             
              :class="{ 'row-selected': selectedGateway?.id === gateway.id }"
            >
              <ion-col size="2">
                <div class="gateway-info">
                  <ion-avatar aria-hidden="true" slot="start" class="table-avatar">
                    <img alt="" :src="gateway.img || OrganizationSVG" />
                  </ion-avatar>
                  <div>
                    <div class="gateway-name">{{ gateway.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="gateway-id">{{ gateway.cs_tenant_id }}</div>
              </ion-col>

              <ion-col size="2">
                <ion-chip
                  :color="getStatusColor(gateway.state)"
                >
                  {{ gateway.group }}
                </ion-chip>
              </ion-col>
              
              <ion-col size="2">
                <div class="location-info">
                  {{ gateway.subscription.name || 'N/A' }}
                </div>
              </ion-col>
              
              <ion-col size="2">
                <div class="time-info">
                  {{ formatTime(gateway.last_seen_at) }}
                </div>
              </ion-col>
              
              <ion-col size="1">
                <div class="devices-info">
                  <ion-icon :icon="icons.phonePortrait" size="small"></ion-icon>
                  {{ gateway.connectedDevices || 0 }}
                </div>
              </ion-col>
              
              <ion-col size="1">
                <ion-button 
                  fill="clear" 
                  size="small"
                  @click.stop="viewGateway(gateway)"
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
          <ion-button @click="fetchGateways" fill="outline">
            Buscar gateways
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, inject } from 'vue'
import API from '@utils/api/api'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useTableSorting } from '@composables/Tables/useTableSorting.js'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { formatTime, getStatusColor } from '@utils/formatters/formatters'
import OrganizationSVG from '@assets/svg/Organization.svg'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Component-specific state
const tenants = ref([])
const loading = ref(false)
const error = ref(null)
const selectedGateway = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(tenants, ['name', 'cs_gateway_id', 'location'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'


// Fetch data from API
const fetchGateways = async () => {
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
    console.log('🔄 Fetching tenants data...')
    
    // Real API call using await
    const response = await API.get(API.TENANT, headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);
    
    tenants.value = mockData
    console.log('✅ Gateways cargados:', mockData.length)
    
  } catch (err) {
    error.value = `❌Error al cargar gateways: ${err.message}`
    console.error('❌ Error fetching tenants:', err)
  } finally {
    loading.value = false
  }
}

// Component-specific methods
const selectGateway = (gateway) => {
  selectedGateway.value = gateway
  console.log('Gateway seleccionado:', gateway)
}

const viewGateway = (gateway) => {
  console.log('Ver detalles del gateway:', gateway)
  // Aquí podrías navegar a una página de detalles
  // router.push(`/tenants/${gateway.id}`)
}

const handleItemRefresh = () => {
  fetchGateways();
};

// Lifecycle
onMounted(async () => {
  console.log('🔧 GatewaysTable component mounted')
  
  // Wait for next tick to ensure DOM is ready
  await nextTick()
  
  // Mark component as mounted
  isMounted.value = true
  
  // Small delay to ensure Ionic page transition is complete
  setTimeout(() => {
    fetchGateways()
  }, 100)
})
</script>

















<style scoped>

.table-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
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
