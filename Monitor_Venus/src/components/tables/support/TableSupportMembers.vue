<template>
  <div>
    <ion-card class="table-card">
      <ion-card-header>
        <ion-card-title>Gestión del equipo de soporte</ion-card-title>
        <ion-card-subtitle>
          {{ loading ? 'Cargando...' : `${members.length} miembros encontrados` }}
        </ion-card-subtitle>
      </ion-card-header>

      <ion-card-content class="custom">
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Obteniendo miembros de soporte...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="error-container">
          <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
          <p>Error: {{ error }}</p>
          <ion-button @click="fetchMembers" fill="outline" color="danger">
            Reintentar
          </ion-button>
        </div>

        <!-- Data -->
        <div v-else-if="members.length > 0">
          <!-- Controls -->
          <div class="table-controls">
            <ion-searchbar
              v-model="searchText"
              placeholder="Buscar miembro..."
              @ionInput="handleSearch"
              show-clear-button="focus"
              class="custom"
            ></ion-searchbar>

            <!-- Desktop button -->
            <div v-if="!isMobile" class="desktop-controls">
              <QuickControl :to-create="true" :to-refresh="true" type="support_member" @itemCreated="fetchMembers" @refresh="fetchMembers" />
            </div>
          </div>

          <!-- Desktop table -->
          <div v-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
              <ion-row class="table-header">
                <ion-col size="3">
                  <strong>Miembro</strong>
                </ion-col>
                <ion-col size="2">
                  <strong>Usuario</strong>
                </ion-col>
                <ion-col size="2">
                  <strong>Rol</strong>
                </ion-col>
                <ion-col size="3">
                  <strong>Alcance</strong>
                </ion-col>
                <ion-col size="2">
                  <strong>Acciones</strong>
                </ion-col>
              </ion-row>

              <ion-row
                v-for="member in paginatedItems"
                :key="member.id"
                class="table-row-stylized"
                v-bind="getItemActivateProps(`/users/${member.user}`, { label: `Ver usuario ${member.username}` })"
              >
                <ion-col size="3">
                  <div class="member-info clickable-member">
                    <ion-avatar class="table-avatar">
                      <img :alt="member.username" :src="member.img || AvatarSVG" />
                    </ion-avatar>
                    <div>
                      <div class="member-name">{{ member.fullName }}</div>
                    </div>
                  </div>
                </ion-col>
                <ion-col size="2">
                  <span class="member-username">@{{ member.username }}</span>
                </ion-col>
                <ion-col size="2">
                  <ion-chip class="role-chip--dark">
                    {{ roleLabel(member.role) }}
                  </ion-chip>
                </ion-col>
                <ion-col size="3">
                  <ion-chip>
                    {{ member.tenantName }}
                  </ion-chip>
                </ion-col>
                <ion-col size="2">
                  <div class="row-actions">
                    <quick-actions
                      type="support_member"
                      :index="member.id"
                      :name="member.fullName"
                      :to-view="`/users/${member.user}`"
                      :initial-data="setInitialData(member)"
                      to-edit
                      to-delete
                      @itemEdited="fetchMembers"
                      @itemDeleted="fetchMembers"
                    />
                  </div>
                </ion-col>
              </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile cards -->
          <div v-else class="mobile-cards">
            <ion-card
              v-for="member in paginatedItems"
              :key="member.id"
              class="member-card"
              :class="getCardClass(true)"
              v-bind="getItemActivateProps(`/users/${member.user}`, { label: `Ver usuario ${member.username}` })"
            >
              <ion-card-content>
                <div class="card-header">
                  <ion-avatar class="card-avatar">
                    <img :alt="member.username" :src="member.img || AvatarSVG" />
                  </ion-avatar>
                  <div class="card-title-section">
                    <h3 class="card-title">{{ member.fullName }}</h3>
                    <p class="card-subtitle">@{{ member.username }}</p>
                  </div>
                </div>

                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Rol:</span>
                    <span class="detail-value">
                      <ion-chip size="small" class="role-chip--dark">
                        {{ roleLabel(member.role) }}
                      </ion-chip>
                    </span>
                  </div>

                  <div class="card-detail-row">
                    <span class="detail-label">Alcance:</span>
                    <span class="detail-value">
                      <ion-chip size="small" color="primary">{{ member.tenantName }}</ion-chip>
                    </span>
                  </div>
                </div>

                <div class="card-actions">
                  <quick-actions
                    type="support_member"
                    :index="member.id"
                    :name="member.fullName"
                    :to-view="`/users/${member.user}`"
                    :initial-data="setInitialData(member)"
                    to-edit
                    to-delete
                    @itemEdited="fetchMembers"
                    @itemDeleted="fetchMembers"
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
            <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
            <ion-button fill="clear" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
              <ion-icon :icon="icons.chevronForward"></ion-icon>
            </ion-button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <ion-icon :icon="icons.people" size="large" color="medium"></ion-icon>
          <h3>No hay miembros de soporte</h3>
          <p>Aún no se han agregado usuarios al equipo de soporte.</p>
          <QuickControl :to-initial="true" type="support_member" text="Nuevo miembro" @itemCreated="fetchMembers" />
        </div>
      </ion-card-content>
    </ion-card>

    <!-- Floating Action Buttons (Mobile Only) -->
    <FloatingActionButtons
      entity-type="support_member"
      @refresh="fetchMembers"
      @itemCreated="fetchMembers"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { IonButton, IonCard } from '@ionic/vue'
import { people, chevronBack, chevronForward, alertCircle } from 'ionicons/icons'
import API from '@utils/api/api'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import { useCardNavigation } from '@composables/useCardNavigation.js'
import AvatarSVG from '@assets/svg/Avatar.svg'

const icons = { ...{ people, chevronBack, chevronForward, alertCircle }, ...inject('icons', {}) }

const { isMobile } = useResponsiveView(768)
const { getCardClass, getItemActivateProps } = useCardNavigation()

const members = ref([])
const loading = ref(false)
const error = ref(null)

const roleLabels = {
  support_agent: 'Agente de Soporte',
  support_manager: 'Gestor de Soporte',
  technician: 'Técnico de Soporte',
  support_technician: 'Técnico de Soporte', // defensive read alias (not from backend)
  other: 'Otro'
}

const roleLabel = (role) => roleLabels[role] || role || 'Desconocido'

const toList = (res) => Array.isArray(res) ? res : (res?.results || res?.data || [])

const userFullName = (u) => {
  if (!u) return null
  const name = [u.name, u.last_name].filter(Boolean).join(' ').trim()
  return name || u.username || u.email || `#${u.id}`
}

const enrich = (raw, usersList, tenantsList) => {
  const user = usersList.find(x => String(x.id) === String(raw.user))
  const tenant = tenantsList.find(t => String(t.id) === String(raw.tenant))
  return {
    ...raw,
    fullName: userFullName(user) || `#${raw.user}`,
    username: user?.username || `#${raw.user}`,
    img: user?.img || null,
    tenantName: raw.tenant ? (tenant?.name || `#${raw.tenant}`) : 'Global (sin tenant)'
  }
}

const fetchMembers = async () => {
  loading.value = true
  error.value = null
  try {
    const [membersRes, usersRes, tenantsRes] = await Promise.all([
      API.get(API.SUPPORT_MEMBERSHIP),
      API.get(API.USER),
      API.get(API.TENANT)
    ])

    const rawMembers = toList(membersRes)
    const usersList = toList(usersRes)
    const tenantsList = toList(tenantsRes)

    members.value = rawMembers.map(m => enrich(m, usersList, tenantsList))
  } catch (err) {
    error.value = `Error al cargar miembros de soporte: ${err.message}`
    console.error('❌ Error fetching support members:', err)
  } finally {
    loading.value = false
  }
}

const setInitialData = (member) => {
  return {
    id: member.id,
    role: member.role,
    tenant: member.tenant
  }
}

const { searchText, filteredItems, handleSearch } = useTableSearch(members, ['fullName', 'username', 'tenantName'])
const { currentPage, totalPages, changePage, paginatedItems } = useTablePagination(filteredItems)

onMounted(() => {
  fetchMembers()
})
</script>

<style scoped>
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
  min-width: 800px;
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

.table-row-stylized {
  border-bottom: 1px solid var(--ion-color-light-shade);
  transition: background-color 0.2s ease;
  cursor: pointer;
}

/* Foco de teclado: la fila completa es activable con Enter/Espacio */
.table-row-stylized:focus-visible,
.clickable-card:focus-visible {
  outline: 2px solid var(--ion-color-primary);
  outline-offset: -2px;
}

.table-row-stylized:hover {
  background-color: var(--ion-color-light-tint);
}

.table-row-stylized ion-col {
  padding: 12px;
  display: flex;
  align-items: center;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-avatar {
  width: 40px;
  height: 40px;
  --background: var(--ion-color-primary);
  color: #fff;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.member-name {
  font-weight: 600;
}

.member-username {
  color: var(--ion-color-medium);
  font-size: 0.85rem;
}

.row-actions {
  display: flex;
  gap: 8px;
}

.mobile-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.member-card {
  flex: 1 1 280px;
  max-width: 100%;
}

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

.clickable-member {
  cursor: pointer;
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
  --background: var(--ion-color-primary);
  color: #fff;
  font-weight: 600;
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
  color: var(--ion-color-medium);
  font-size: 0.85rem;
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.page-info {
  color: var(--ion-color-medium);
  font-size: 0.9rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  text-align: center;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  text-align: center;
}

.error-container ion-icon {
  font-size: 48px;
  opacity: 0.5;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
}

ion-chip.role-chip--dark {
  --background: #27272a; /* zinc-800 */
  --color: #ffffff;
  --background-activated: #27272a;
  color: #ffffff;
}

ion-chip.role-chip--dark:hover,
ion-chip.role-chip--dark:focus {
  --background: #3f3f46; /* zinc-700 */
  color: #ffffff;
}
</style>
