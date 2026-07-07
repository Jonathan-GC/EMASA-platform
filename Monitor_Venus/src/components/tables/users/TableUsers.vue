<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Usuarios registrados en el sistema</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${users.length} ${users.length === 1 ? 'usuario encontrado' : 'usuarios encontrados'}` }}
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
            <ion-searchbar
              v-model="searchText"
              placeholder="Buscar usuario..."
              @ionInput="handleSearch"
              show-clear-button="focus"
              class="custom"
            ></ion-searchbar>

            <!-- Desktop buttons -->
            <div v-if="!isMobile" class="desktop-controls">
              <ion-button @click="fetchUsers" fill="clear" shape="round">
                <ion-icon :icon="icons.refresh" slot="icon-only"></ion-icon>
              </ion-button>
              <QuickControl
                :toCreate="true"
                type="user"
                @itemCreated="handleItemRefresh"
              />
            </div>
          </div>

          <!-- Table using ion-grid (Desktop) -->
          <div v-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
            <!-- Header -->
            <ion-row class="table-header">
              <ion-col size="2" @click="sortBy('username')" class="sortable">
                <strong>Usuario</strong>
                <ion-icon
                  :icon="sortOrder.username === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'username'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('name')" class="sortable">
                <strong>Nombre Completo</strong>
                <ion-icon
                  :icon="sortOrder.name === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'name'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2" @click="sortBy('email')" class="sortable">
                <strong>Email</strong>
                <ion-icon
                  :icon="sortOrder.email === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'email'"
                ></ion-icon>
              </ion-col>
              <ion-col size="1">
                <strong>Tenant</strong>
              </ion-col>
              <ion-col size="2" @click="sortBy('code')" class="sortable">
                <strong>Código</strong>
                <ion-icon
                  :icon="sortOrder.code === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'code'"
                ></ion-icon>
              </ion-col>
              <ion-col size="1" @click="sortBy('is_active')" class="sortable">
                <strong>Estado</strong>
                <ion-icon
                  :icon="sortOrder.is_active === 'asc' ? icons.chevronUp : icons.chevronDown"
                  v-if="sortField === 'is_active'"
                ></ion-icon>
              </ion-col>
              <ion-col size="2">
                <strong>Acciones</strong>
              </ion-col>
            </ion-row>

            <!-- Data rows -->
            <ion-row
              v-for="user in paginatedItems"
              :key="user.id"
              class="table-row-stylized"
              :class="{ 'row-selected': selectedUser?.id === user.id }"
            >
              <ion-col size="2">
                <div class="user-info">
                  <ion-avatar class="table-avatar">
                    <img :alt="user.username" :src="user.img || AvatarSVG" />
                  </ion-avatar>
                  <div class="user-username">{{ user.username }}</div>
                </div>
              </ion-col>
              
              <ion-col size="2">
                <div class="user-name">{{ `${user.name} ${user.last_name}` }}</div>
              </ion-col>
              
              <ion-col size="2">
                <div class="user-email">{{ user.email }}</div>
              </ion-col>
              
              <ion-col size="1">
                <ion-chip size="small">
                  {{ user.tenant_name }}
                </ion-chip>
              </ion-col>
              
              <ion-col size="2">
                <div class="user-code">{{ user.code }}</div>
              </ion-col>
              
              <ion-col size="1">
                <ion-chip :color="user.is_active ? 'success' : 'secondary'">
                  {{ formatActiveStatus(user.is_active) }}
                </ion-chip>
              </ion-col>

              <ion-col size="2">
                <QuickActions 
                  type="user"
                  :index="user.id" 
                  :name="user.username"
                  to-edit
                  to-toggle
                  :status="user.is_active"
                  :initial-data="setInitialData(user)"
                  @item-edited="handleItemRefresh"
                  @item-toggled="handleItemRefresh"

                />
              </ion-col>
            </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile Card View -->
          <div v-else class="mobile-cards">
            <ion-card 
              v-for="user in paginatedItems" 
              :key="user.id" 
              class="user-card"
              :class="getCardClass(true)"
              @click="(event) => getCardClickHandler(`/users/${user.id}`)(event)"
            >
              <ion-card-content>
                <!-- Header with avatar and name -->
                <div class="card-header">
                  <ion-avatar class="card-avatar">
                    <img :alt="user.username" :src="user.img || AvatarSVG" />
                  </ion-avatar>
                  <div class="card-title-section">
                    <h3 class="card-title">{{ `${user.name} ${user.last_name}` }}</h3>
                    <p class="card-subtitle">@{{ user.username }}</p>
                  </div>
                  <ion-chip :color="user.is_active ? 'success' : 'danger'" class="card-chip">
                    {{ formatActiveStatus(user.is_active) }}
                  </ion-chip>
                </div>

                <!-- Card details -->
                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Código:</span>
                    <span class="detail-value">{{ user.code }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Email:</span>
                    <span class="detail-value">{{ user.email }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Teléfono:</span>
                    <span class="detail-value">{{ user.phone_code }} {{ user.phone }}</span>
                  </div>
                  
                  <div class="card-detail-row">
                    <span class="detail-label">Tenant:</span>
                    <span class="detail-value">
                      <ion-chip size="small" color="primary">{{ user.tenant_name }}</ion-chip>
                    </span>
                  </div>
                </div>

                <!-- Card actions -->
                <div class="card-actions">
                  <QuickActions 
                    type="user"
                    :index="user.id" 
                    :name="user.username"
                    to-edit
                    to-delete
                    :initial-data="setInitialData(user)"
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
          <ion-icon :icon="icons.people" size="large" color="medium"></ion-icon>
          <h3>No hay usuarios</h3>
          <p>No se encontraron usuarios en el sistema</p>
          <QuickControl
            :toCreate="true"
            type="user"
            @itemCreated="handleItemRefresh"
          />
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons 
      v-if="isMobile"
      entity-type="user"
      @refresh="fetchUsers"
      @itemCreated="handleItemRefresh"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, inject } from 'vue'
import { useRouter } from 'vue-router'
import API from '@utils/api/api'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useTableSorting } from '@composables/Tables/useTableSorting.js'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { useCardNavigation } from '@composables/useCardNavigation.js'
import { formatActiveStatus } from '@utils/formatters/formatters'
import AvatarSVG from '@assets/svg/Avatar.svg'
import QuickControl from '../../operators/quickControl.vue'
import QuickActions from '../../operators/quickActions.vue'
import FloatingActionButtons from '../../operators/FloatingActionButtons.vue'

// Inject icons
const icons = inject('icons', {})
const router = useRouter()

// Responsive view detection
const { isMobile } = useResponsiveView(768)

// Card navigation composable
const { getCardClickHandler, getCardClass } = useCardNavigation()

// Component-specific state
const users = ref([])
const loading = ref(false)
const error = ref(null)
const selectedUser = ref(null)
const isMounted = ref(false)

// Transform users data to include searchable status text
const searchableUsers = computed(() => {
  return users.value.map(user => ({
    ...user,
    statusText: formatActiveStatus(user.is_active)
  }))
})

// Table composables
const { searchText, filteredItems, handleSearch } = useTableSearch(searchableUsers, ['code', 'username', 'email', 'name', 'last_name', 'tenant', 'statusText'])
const { sortField, sortOrder, sortBy, applySorting } = useTableSorting()
const sortedItems = computed(() => applySorting(filteredItems.value))
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(sortedItems)

// Set initial data for edit form
const setInitialData = (user) => {
  return {
    code: user.code,
    username: user.username,
    email: user.email,
    name: user.name,
    last_name: user.last_name,
    phone: user.phone,
    phone_code: user.phone_code,
    country: user.country,
    tenant: user.tenant,
    is_active: user.is_active,
    img: user.img,
    address: user.address
  }
}

// Fetch data from API
const fetchUsers = async () => {
  // Ensure component is mounted before fetching
  if (!isMounted.value) {
    console.log('⏳ Component not ready, waiting...')
    return
  }

  loading.value = true
  error.value = null

  try {
    console.log('🔄 Fetching users data...')

    // Real API call using await
    const response = await API.get(API.USER)
    // Ensure response is an array
    const userData = Array.isArray(response) ? response : (response?.data || [])

    users.value = userData
    console.log('✅ Usuarios cargados:', userData.length)

  } catch (err) {
    error.value = `❌ Error al cargar usuarios: ${err.message}`
    console.error('❌ Error fetching users:', err)
  } finally {
    loading.value = false
  }
}

// Handle item refresh
const handleItemRefresh = () => {
  fetchUsers()
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 TableUsers component mounted')

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

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.user-username {
  font-weight: 500;
  font-size: 0.9rem;
}

.user-code {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  font-family: monospace;
}

.user-email {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
}

.user-name {
  font-size: 0.9rem;
  font-weight: 500;
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

  .user-info {
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

.user-card {
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-card ion-card-content {
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
  overflow: hidden;
  text-overflow: ellipsis;
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
