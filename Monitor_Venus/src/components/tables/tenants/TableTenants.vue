<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Clientes registrados en el sistema</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${tenants.length} ${tenants.length === 1 ? 'cliente encontrado' : 'clientes encontrados'}` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de los clientes...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchTenants" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="tenants.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar v-model="searchText" placeholder="Buscar cliente..." @ionInput="handleSearch"
              show-clear-button="focus" class="custom"></ion-searchbar>

            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchTenants" fill="clear" shape="round">
                <ion-icon :icon="icons.refresh" slot="icon-only"></ion-icon>
              </ion-button>
              <QuickControl :toCreate="true" type="tenant" @itemCreated="handleItemRefresh" />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <div class="table-wrapper" v-if="!isMobile">
            <ion-grid class="data-table">
              <!-- Header -->
              <ion-row class="table-header">


              <ion-col size="2" @click="sortBy('name')" class="sortable">
                <strong>Nombre</strong>
                <ion-icon :icon="sortOrder.name === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('cs_tenant_id')" class="sortable">
                <strong>ID</strong>
                <ion-icon :icon="sortOrder.cs_tenant_id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'cs_tenant_id'"></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>subscription</strong>
              </ion-col>
              <ion-col size="2" @click="sortBy('lastSeen')" class="sortable">
                <strong>Última conexión</strong>
                <ion-icon :icon="sortOrder.lastSeen === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'lastSeen'"></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Dispositivos</strong>
              </ion-col>
              <ion-col size="2">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row v-for="tenant in paginatedItems" :key="tenant.id" class="table-row-stylized"
              :class="{ 'row-selected': selectedTenant?.id === tenant.id }">
              <ion-col size="2">
                <div class="gateway-info">
                  <ion-avatar aria-hidden="true" slot="start" class="table-avatar">
                    <img alt="" :src="tenant.img || OrganizationSVG" />
                  </ion-avatar>
                  <div>
                    <div class="gateway-name">{{ tenant.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="gateway-id">{{ tenant.id }}</div>
              </ion-col>

              <ion-col size="2">
                <div class="location-info">
                  {{ tenant.subscription.name || 'N.A' }}
                </div>
              </ion-col>

              <ion-col size="2">
                <div class="time-info">
                  {{ formatTime(tenant.last_seen_at) }}
                </div>
              </ion-col>

              <ion-col size="1">
                <div class="devices-info">
                  <ion-icon :icon="icons.phonePortrait" size="small"></ion-icon>
                  {{ tenant.connectedDevices || 0 }}
                </div>
              </ion-col>

              <ion-col size="2">

                <QuickActions 
                  type="tenant"
                  :index="tenant.id" 
                  :name="tenant.name" 
                  to-edit
                  to-delete
                  :initial-data="setInitialData(tenant)"
                  @item-edited="handleItemRefresh"
                  @item-deleted="handleItemRefresh"

                />
              </ion-col>
            </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card 
              v-for="tenant in paginatedItems" 
              :key="tenant.id" 
              class="tenant-card"
              :class="getCardClass(true)"
            >
              <ion-card-content>
                <!-- Header with avatar and name -->
                <div class="card-header">
                  <ion-avatar class="card-avatar">
                    <img alt="" :src="tenant.img || OrganizationSVG" />
                  </ion-avatar>
                  <div class="card-title-section">
                    <h3 class="card-title">{{ tenant.name }}</h3>
                    <p class="card-subtitle">ID: {{ tenant.id }}</p>
                  </div>
                  <ion-chip :color="getStatusColor(tenant.state)" class="card-chip">
                    {{ tenant.group }}
                  </ion-chip>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Subscription:</span>
                    <span class="detail-value">{{ tenant.subscription.name || 'N.A' }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Última conexión:</span>
                    <span class="detail-value">{{ formatTime(tenant.last_seen_at) }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Dispositivos:</span>
                    <span class="detail-value">
                      <ion-icon :icon="icons.phonePortrait" size="small"></ion-icon>
                      {{ tenant.connectedDevices || 0 }}
                    </span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <QuickActions 
                    type="tenant"
                    :index="tenant.id" 
                    :name="tenant.name"
                    to-edit
                    to-delete
                    :initial-data="setInitialData(tenant)"
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
          <h3>No hay clientes</h3>
          <p>No se encontraron clientes en el sistema</p>
          <QuickControl :toCreate="true" type="tenant" @itemCreated="handleItemRefresh" />
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="tenant"
      @refresh="fetchTenants"
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
import { useCardNavigation } from '@composables/useCardNavigation.js'
import { formatTime, getStatusColor } from '@utils/formatters/formatters'
import OrganizationSVG from '@assets/svg/Organization.svg'
import QuickActions from '../../operators/quickActions.vue'
import QuickControl from '../../operators/quickControl.vue'
import FloatingActionButtons from '../../operators/FloatingActionButtons.vue'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Card navigation composable
const { getCardClickHandler, getCardClass } = useCardNavigation()

// Responsive view detection
const { isMobile, isTablet, isDesktop } = useResponsiveView(768)

// Component-specific state
const tenants = ref([])
const loading = ref(false)
const error = ref(null)
const selectedTenant = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(tenants, ['name', 'cs_tenant_id', 'subscription.name, '])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'


// Fetch data from API
const fetchTenants = async () => {
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

const setInitialData = (gateway) => {
  return {
    name: gateway.name,
    description: gateway.description,
    subscription_id: gateway.subscription.id,
    img: gateway.img
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
  fetchTenants();
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
    fetchTenants()
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

.tenant-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tenant-card ion-card-content {
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

.card-avatar {
  width: 48px;
  height: 48px;
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

.card-chip {
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
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}

/* Clickable Card Styles */
.clickable-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}

.clickable-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.clickable-card:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

</style>
