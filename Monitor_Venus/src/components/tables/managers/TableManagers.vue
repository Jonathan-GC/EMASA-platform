<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>🌐 Usuarios del Tenant - Datos desde API</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${users.length} tenants encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de los usuarios...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchUsers" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="users.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar v-model="searchText" placeholder="Buscar gateway..." @ionInput="handleSearch"
              show-clear-button="focus" class="custom"></ion-searchbar>

            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchUsers" fill="clear">
                <ion-icon :icon="icons.refresh"></ion-icon>
              </ion-button>
              <QuickControl :toCreate="true" type="manager" @itemCreated="handleItemRefresh" />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <ion-grid v-if="!isMobile" class="data-table">
            <!-- Header -->
            <ion-row class="table-header">


              <ion-col size="2" @click="sortBy('name')" class="sortable">
                <strong>Correo</strong>
                <ion-icon :icon="sortOrder.email === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('cs_tenant_id')" class="sortable">
                <strong>ID</strong>
                <ion-icon :icon="sortOrder.cs_user_id === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'cs_user_id'"></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('status')" class="sortable">
                <strong>Cliente</strong>
                <ion-icon :icon="sortOrder.status === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'status'"></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>Estado</strong>
              </ion-col>
              <ion-col size="2" @click="sortBy('note')" class="sortable">
                <strong>Nota</strong>
                <ion-icon :icon="sortOrder.note === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'note'"></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row v-for="user in paginatedItems" :key="user.id" class="table-row-stylized"
              :class="{ 'row-selected': selectedUser?.id === user.id }">
              <ion-col size="2">
                <div class="gateway-info">
                  <div>
                    <div class="gateway-name">{{ user.email }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="gateway-id">{{ user.cs_user_id }}</div>
              </ion-col>

              <ion-col size="2">
                <ion-chip>
                  {{ user.workspace.tenant || 'N.A' }}
                </ion-chip>
              </ion-col>

              <ion-col size="2">
                <div class="location-info">
                  <ion-chip :color="getStatusColor(formatActiveStatus(user.is_active))">
                    {{ formatActiveStatus(user.is_active) || 'N.A' }}
                  </ion-chip>
                </div>
              </ion-col>

              <ion-col size="2">
                <div class="time-info">
                  {{ user.note || 'Ninguna' }}
                </div>
              </ion-col>

              <ion-col size="1">
                <QuickActions :toView="true" />
              </ion-col>
            </ion-row>
          </ion-grid>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card v-for="user in paginatedItems" :key="user.id" class="manager-card">
              <ion-card-content>
                <!-- Header with email and status -->
                <div class="card-header">
                  <div class="card-title-section">
                    <h3 class="card-title">{{ user.email }}</h3>
                    <p class="card-subtitle">ID: {{ user.cs_user_id }}</p>
                  </div>
                  <ion-chip :color="getStatusColor(formatActiveStatus(user.is_active))" class="card-chip-status">
                    {{ formatActiveStatus(user.is_active) || 'N.A' }}
                  </ion-chip>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Cliente:</span>
                    <span class="detail-value">
                      <ion-chip size="small">{{ user.workspace.tenant || 'N.A' }}</ion-chip>
                    </span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Nota:</span>
                    <span class="detail-value">{{ user.note || 'Ninguna' }}</span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <QuickActions :toView="true" />
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
          <h3>No hay gateways</h3>
          <p>No se encontraron gateways en el sistema</p>
          <ion-button @click="fetchUsers" fill="outline">
            Buscar gateways
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="manager"
      @refresh="fetchUsers"
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
import { formatTime, getStatusColor, formatActiveStatus } from '@utils/formatters/formatters'
import AvatarSVG from '@assets/svg/Avatar.svg'
import QuickControl from '../../operators/quickControl.vue'
import FloatingActionButtons from '../../operators/FloatingActionButtons.vue'

// Acceso a los iconos desde el plugin registrado en Vue usando inject
const icons = inject('icons', {})

// Responsive view detection
const { isMobile, isTablet, isDesktop } = useResponsiveView(768)

// Component-specific state
const users = ref([])
const loading = ref(false)
const error = ref(null)
const selectedUser = ref(null)
const isMounted = ref(false)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(users, ['name', 'cs_gateway_id', 'location'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.ejemplo.com'



// Fetch data from API
const fetchUsers = async () => {
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
    console.log('🔄 Fetching users data...')

    // Real API call using await
    const response = await API.get(API.API_USER, headers);
    // Ensure response is an array, if not, wrap it or use a default
    const mockData = Array.isArray(response) ? response : (response?.data || []);

    users.value = mockData
    console.log('✅ Gateways cargados:', mockData.length)

  } catch (err) {
    error.value = `❌Error al cargar gateways: ${err.message}`
    console.error('❌ Error fetching users:', err)
  } finally {
    loading.value = false
  }
}

// Component-specific methods
const selectUser = (user) => {
  selectedUser.value = user
  console.log('Gateway seleccionado:', user)
}

const viewUser = (user) => {
  console.log('Ver detalles del gateway:', user)
  // Aquí podrías navegar a una página de detalles
  // router.push(`/users/${gateway.id}`)
}

const handleItemRefresh = () => {
  fetchUsers();
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
    fetchUsers()
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

.data-table {
  border: 1px solid var(--ion-color-light);
  border-radius: 8px;
  overflow: hidden;
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

.manager-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.manager-card ion-card-content {
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
  display: flex;
  align-items: center;
  gap: 4px;
  text-align: right;
  word-break: break-word;
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
</style>
