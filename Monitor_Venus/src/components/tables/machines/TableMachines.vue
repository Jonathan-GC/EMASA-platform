<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>🌐 Machines - Datos desde API</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${máquinas.length} máquinas encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content>
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
        <div v-else-if="máquinas.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar 
              v-model="searchText"
              placeholder="Buscar máquina..."
              @ionInput="handleSearch"
              show-clear-button="focus"
            ></ion-searchbar>
            
            <ion-button @click="fetchmáquinas" fill="clear">
              <ion-icon :icon="icons.refresh"></ion-icon>
            </ion-button>

            <QuickControl
                :toCreate="true"
                type="machine"
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
                    <div class="machine-name">{{ machine.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="machine-id">{{ machine.id }}</div>
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
                <ion-button 
                  fill="clear" 
                  size="small"
                  @click.stop="viewmachine(machine)"
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
          <h3>No hay máquinas</h3>
          <p>No se encontraron máquinas en el sistema</p>
          <ion-button @click="fetchmáquinas" fill="outline">
            Buscar máquinas
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

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Component-specific state
const máquinas = ref([])
const loading = ref(false)
const error = ref(null)
const selectedmachine = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(máquinas, ['name', 'cs_machine_id', 'location'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'



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
    
    máquinas.value = mockData
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
</style>
