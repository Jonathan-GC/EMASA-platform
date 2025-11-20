<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>🎭 Roles del Sistema</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${roles.length} roles encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo datos de roles...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchRoles" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data table -->
        <div v-else-if="roles.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar 
              v-model="searchText"
              placeholder="Buscar rol..."
              @ionInput="handleSearch"
              show-clear-button="focus"
              class="custom"
            ></ion-searchbar>
            
            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchRoles" fill="clear" shape="round">
                <ion-icon :icon="icons.refresh" slot="icon-only"></ion-icon>
              </ion-button>
              <QuickControl
                  :toCreate="true"
                  type="role"
                  @itemCreated="handleItemRefresh"
              />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <div class="table-wrapper" v-if="!isMobile">
          <ion-grid class="data-table">
            <!-- Header -->
            <ion-row class="table-header">
              <ion-col size="2.5" @click="sortBy('name')" class="sortable">
                <strong>Nombre</strong>
                <ion-icon
                  :icon="sortOrder.name === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"
                ></ion-icon>
              </ion-col>
              <ion-col size="3.5">
                <strong>Descripción</strong>
              </ion-col>
              <ion-col size="1.5">
                <strong>Color</strong>
              </ion-col>
              <ion-col size="1.5" @click="sortBy('users_count')" class="sortable">
                <strong>Usuarios</strong>
                <ion-icon 
                  :icon="sortOrder.users_count === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'users_count'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row 
              v-for="role in paginatedItems" 
              :key="role.id"
              class="table-row-stylized"
              :class="{ 'row-selected': selectedRole?.id === role.id }"
            >
              <ion-col size="2.5">
                <div class="role-info">
                  <ion-avatar 
                    aria-hidden="true" 
                    class="table-avatar role-avatar"
                    :style="{ backgroundColor: role.color || '#5865F2' }"
                  >
                    <ion-icon 
                      v-if="!role.img"
                      :icon="icons.shield" 
                      class="avatar-icon"
                    ></ion-icon>
                    <img v-else alt="" :src="role.img" />
                  </ion-avatar>
                  <div>
                    <div class="role-name">{{ role.name }}</div>
                  </div>
                </div>
              </ion-col>
              <ion-col size="3.5">
                <div class="role-description">
                  {{ role.description || 'Sin descripción' }}
                </div>
              </ion-col>
              <ion-col size="1.5">
                <ion-chip 
                  :style="{ 
                    backgroundColor: role.color || '#5865F2',
                    color: getContrastColor(role.color || '#5865F2')
                  }"
                  class="role-color-chip"
                >
                  {{ role.color || '#5865F2' }}
                </ion-chip>
              </ion-col>
              <ion-col size="1.5">
                <div class="users-count">
                  <ion-icon :icon="icons.people"></ion-icon>
                  <span>{{ role.users_count || 0 }}</span>
                </div>
              </ion-col>
              <ion-col size="2">
                <div class="action-buttons">
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="openPermissionsManager(role)"
                    title="Gestionar permisos"
                  >
                    <ion-icon :icon="icons.key"></ion-icon>
                  </ion-button>
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="openWorkspaceMembershipForm(role)"
                    title="Asignar usuario a workspace"
                  >
                    <ion-icon :icon="icons.person_add"></ion-icon>
                  </ion-button>
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="viewRole(role)"
                    title="Ver detalles"
                  >
                    <ion-icon :icon="icons.eye"></ion-icon>
                  </ion-button>
                </div>
              </ion-col>
            </ion-row>
          </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card 
              v-for="role in paginatedItems" 
              :key="role.id" 
              class="role-card"
            >
              <ion-card-content>
                <!-- Header with avatar and name -->
                <div class="card-header">
                  <ion-avatar 
                    class="card-avatar"
                    :style="{ backgroundColor: role.color || '#5865F2' }"
                  >
                    <ion-icon 
                      v-if="!role.img"
                      :icon="icons.shield" 
                      class="avatar-icon"
                    ></ion-icon>
                    <img v-else alt="" :src="role.img" />
                  </ion-avatar>
                  <div class="card-title-section">
                    <h3 class="card-title">{{ role.name }}</h3>
                    <p class="card-subtitle">{{ role.description || 'Sin descripción' }}</p>
                  </div>
                  <ion-chip 
                    :style="{ 
                      backgroundColor: role.color || '#5865F2',
                      color: getContrastColor(role.color || '#5865F2')
                    }"
                    class="card-chip"
                  >
                    {{ role.color || '#5865F2' }}
                  </ion-chip>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Usuarios:</span>
                    <span class="detail-value">
                      <ion-icon :icon="icons.people"></ion-icon>
                      {{ role.users_count || 0 }}
                    </span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="openPermissionsManager(role)"
                  >
                    <ion-icon :icon="icons.key"></ion-icon>
                    Permisos
                  </ion-button>
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="openWorkspaceMembershipForm(role)"
                  >
                    <ion-icon :icon="icons.personAdd"></ion-icon>
                    Asignar
                  </ion-button>
                  <ion-button 
                    fill="clear" 
                    size="small"
                    @click.stop="viewRole(role)"
                  >
                    <ion-icon :icon="icons.eye"></ion-icon>
                    Ver
                  </ion-button>
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
          <ion-icon :icon="icons.shield" size="large" color="medium"></ion-icon>
          <h3>No hay roles</h3>
          <p>No se encontraron roles en el sistema</p>
          <ion-button @click="fetchRoles" fill="outline">
            Buscar roles
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="role"
      @refresh="fetchRoles"
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
import QuickControl from '@components/operators/QuickControl.vue'
import FloatingActionButtons from '@components/operators/FloatingActionButtons.vue'
import RolePermissionsManager from '@components/forms/permissions/RolePermissionsManager.vue'
import WorkspaceMembershipForm from '@components/forms/roles/WorkspaceMembershipForm.vue'
import { IonAvatar, modalController } from '@ionic/vue'

// Inject icons
const icons = inject('icons', {})

// Responsive view detection
const { isMobile, isTablet, isDesktop } = useResponsiveView(768)

// Component state
const roles = ref([])
const loading = ref(false)
const error = ref(null)
const selectedRole = ref(null)
const isMounted = ref(false)
const permissionsModal = ref(null)

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(roles, ['name', 'description'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// Fetch data from API
const fetchRoles = async () => {
  if (!isMounted.value) {
    console.log('⏳ Component not ready, waiting...')
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    console.log('🔄 Fetching roles data...')
    
    const response = await API.get(API.ROLE)
    const mockData = Array.isArray(response) ? response : (response?.data || [])
    
    roles.value = mockData
    console.log('✅ Roles loaded:', mockData.length)
    
  } catch (err) {
    error.value = `Error al cargar roles: ${err.message}`
    console.error('❌ Error fetching roles:', err)
  } finally {
    loading.value = false
  }
}

// Utility function to get contrasting text color
const getContrastColor = (hexColor) => {
  if (!hexColor) return '#FFFFFF'
  
  // Remove # if present
  const hex = hexColor.replace('#', '')
  
  // Convert to RGB
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  
  // Calculate luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  
  return luminance > 0.5 ? '#000000' : '#FFFFFF'
}

// Component methods
const selectRole = (role) => {
  selectedRole.value = role
  console.log('Role selected:', role)
}

const viewRole = (role) => {
  console.log('View role details:', role)
  // Navigate to role details page
}

const openPermissionsManager = async (role) => {
  console.log('Opening permissions manager for role:', role.name)
  
  const modal = await modalController.create({
    component: RolePermissionsManager,
    componentProps: {
      role: role
    },
    cssClass: 'full-modal'
  })
  
  modal.onDidDismiss().then(() => {
    console.log('Permissions manager closed')
    fetchRoles() // Refresh roles after permissions update
  })
  
  await modal.present()
}

const openWorkspaceMembershipForm = async (role) => {
  console.log('Opening workspace membership form for role:', role.name)
  
  const modal = await modalController.create({
    component: WorkspaceMembershipForm,
    componentProps: {
      initialData: {
        role_id: role.id
      }
    },
    cssClass: 'full-modal'
  })
  
  modal.onDidDismiss().then(() => {
    console.log('Workspace membership form closed')
    // Optionally refresh data if needed
  })
  
  await modal.present()
}

const handleItemRefresh = () => {
  fetchRoles()
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 TableRoles component mounted')
  
  await nextTick()
  isMounted.value = true
  
  setTimeout(() => {
    fetchRoles()
  }, 100)
})
</script>

<style scoped>
.table-card {
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
  gap: 16px;
  margin-bottom: 16px;
}

.table-controls ion-searchbar {
  flex: 1;
  min-width: 200px;
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

.table-header {
  background-color: var(--ion-color-light);
  font-weight: 600;
  border-bottom: 2px solid var(--ion-color-medium);
}

.table-header ion-col {
  padding: 16px 12px;
}

.sortable {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.sortable:hover {
  background-color: var(--ion-color-light-tint);
}

.table-row-stylized {
  border-bottom: 1px solid var(--ion-color-light-shade);
  transition: background-color 0.2s ease;
}

.table-row-stylized:hover {
  background-color: var(--ion-color-light-tint);
  cursor: pointer;
}

.row-selected {
  background-color: var(--ion-color-primary-tint);
}

.table-row-stylized ion-col {
  padding: 12px;
  display: flex;
  align-items: center;
}

.role-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--ion-color-light-shade);
}

.role-avatar {
  color: white;
}

.avatar-icon {
  font-size: 24px;
  color: white;
}

.role-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--ion-color-dark);
}

.role-description {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-color-chip {
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.users-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
}

.users-count ion-icon {
  font-size: 18px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-buttons ion-button {
  --padding-start: 8px;
  --padding-end: 8px;
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-state ion-icon {
  opacity: 0.5;
}

/* Mobile Cards Styles */
.mobile-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.role-card ion-card-content {
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
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--ion-color-light-shade);
}

.card-avatar .avatar-icon {
  font-size: 28px;
  color: white;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-chip {
  flex-shrink: 0;
  height: 24px;
  font-size: 0.7rem;
  font-weight: 600;
  font-family: 'Courier New', monospace;
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
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--ion-color-light);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .table-controls {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
