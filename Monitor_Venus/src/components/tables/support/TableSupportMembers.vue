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
              <ion-button color="secondary" fill="solid" shape="round" class="mx-2" @click="openCreate">
                <ion-icon :icon="icons.add" slot="icon-only"></ion-icon>
              </ion-button>
            </div>
          </div>

          <!-- Desktop table -->
          <div v-if="!isMobile" class="table-wrapper">
            <ion-grid class="data-table">
              <ion-row class="table-header">
                <ion-col size="4">
                  <strong>Miembro</strong>
                </ion-col>
                <ion-col size="2">
                  <strong>Rol</strong>
                </ion-col>
                <ion-col size="3">
                  <strong>Alcance</strong>
                </ion-col>
                <ion-col size="3">
                  <strong>Acciones</strong>
                </ion-col>
              </ion-row>

              <ion-row v-for="member in paginatedItems" :key="member.id" class="table-row-stylized">
                <ion-col size="4">
                  <div class="member-info">
                    <ion-avatar class="table-avatar" color="primary">
                      {{ avatarInitials(member) }}
                    </ion-avatar>
                    <div>
                      <div class="member-name">{{ member.fullName }}</div>
                      <div class="member-username">@{{ member.username }}</div>
                    </div>
                  </div>
                </ion-col>
                <ion-col size="2">
                  <ion-badge :color="roleColor(member.role)">
                    {{ roleLabel(member.role) }}
                  </ion-badge>
                </ion-col>
                <ion-col size="3">
                  <ion-chip>
                    {{ member.tenantName }}
                  </ion-chip>
                </ion-col>
                <ion-col size="3">
                  <div class="row-actions">
                    <ion-button fill="outline" size="small" @click="openEdit(member)">
                      <ion-icon :icon="icons.create" slot="start"></ion-icon>
                      Editar
                    </ion-button>
                    <ion-button fill="outline" size="small" color="danger" :disabled="deletingId === member.id" @click="confirmDelete(member)">
                      <ion-spinner v-if="deletingId === member.id" name="crescent"></ion-spinner>
                      <ion-icon v-else :icon="icons.trash" slot="start"></ion-icon>
                      Eliminar
                    </ion-button>
                  </div>
                </ion-col>
              </ion-row>
            </ion-grid>
          </div>

          <!-- Mobile cards -->
          <div v-else class="mobile-cards">
            <ion-card v-for="member in paginatedItems" :key="member.id" class="member-card">
              <ion-card-content>
                <div class="card-header">
                  <ion-avatar class="card-avatar" color="primary">
                    {{ avatarInitials(member) }}
                  </ion-avatar>
                  <div class="card-title-section">
                    <h3 class="card-title">{{ member.fullName }}</h3>
                    <p class="card-subtitle">@{{ member.username }}</p>
                  </div>
                  <ion-badge :color="roleColor(member.role)" class="card-chip">
                    {{ roleLabel(member.role) }}
                  </ion-badge>
                </div>

                <div class="card-details">
                  <div class="card-detail-row">
                    <span class="detail-label">Alcance:</span>
                    <span class="detail-value">{{ member.tenantName }}</span>
                  </div>
                </div>

                <div class="card-actions">
                  <ion-button fill="outline" size="small" @click="openEdit(member)">
                    <ion-icon :icon="icons.create" slot="start"></ion-icon>
                    Editar
                  </ion-button>
                  <ion-button fill="outline" size="small" color="danger" :disabled="deletingId === member.id" @click="confirmDelete(member)">
                    <ion-spinner v-if="deletingId === member.id" name="crescent"></ion-spinner>
                    <ion-icon v-else :icon="icons.trash" slot="start"></ion-icon>
                    Eliminar
                  </ion-button>
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
          <ion-button color="secondary" fill="solid" shape="round" @click="openCreate">
            <ion-icon :icon="icons.add" slot="start"></ion-icon>
            Nuevo miembro
          </ion-button>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { IonButton, IonCard, modalController, alertController, toastController } from '@ionic/vue'
import { add, create, trash, people, chevronBack, chevronForward, alertCircle } from 'ionicons/icons'
import API from '@utils/api/api'
import { useTableSearch } from '@composables/Tables/useTableSearch.js'
import { useTablePagination } from '@composables/Tables/useTablePagination.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import SupportMembershipForm from '@components/forms/support/SupportMembershipForm.vue'

const icons = { ...{ add, create, trash, people, chevronBack, chevronForward, alertCircle }, ...inject('icons', {}) }

const { isMobile } = useResponsiveView(768)

const members = ref([])
const loading = ref(false)
const error = ref(null)
const deletingId = ref(null)

const roleLabels = {
  support_agent: 'Agente de Soporte',
  support_manager: 'Gestor de Soporte',
  technician: 'Técnico',
  other: 'Otro'
}

const roleColors = {
  support_agent: 'medium',
  support_manager: 'secondary',
  technician: 'success',
  other: 'medium'
}

const roleLabel = (role) => roleLabels[role] || role || 'Desconocido'
const roleColor = (role) => roleColors[role] || 'medium'

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

const avatarInitials = (member) => {
  const parts = (member.fullName || '').split(' ').filter(Boolean)
  return parts.length > 1 ? `${parts[0][0]}${parts[1][0]}`.toUpperCase() : (parts[0]?.[0] || '#').toUpperCase()
}

const openCreate = async () => {
  const modal = await modalController.create({
    component: SupportMembershipForm,
    componentProps: { mode: 'create' },
    cssClass: 'full-modal'
  })
  modal.onDidDismiss().then((res) => {
    if (res.data?.created) fetchMembers()
  })
  await modal.present()
}

const openEdit = async (member) => {
  const modal = await modalController.create({
    component: SupportMembershipForm,
    componentProps: {
      mode: 'edit',
      initialData: {
        id: member.id,
        role: member.role,
        tenant: member.tenant
      }
    },
    cssClass: 'full-modal'
  })
  modal.onDidDismiss().then((res) => {
    if (res.data?.edited) fetchMembers()
  })
  await modal.present()
}

const confirmDelete = async (member) => {
  const alert = await alertController.create({
    header: 'Eliminar miembro de soporte',
    message: `¿Estás seguro de que deseas remover a ${member.fullName} del equipo de soporte?`,
    buttons: [
      { text: 'Cancelar', role: 'cancel' },
      {
        text: 'Eliminar',
        role: 'confirm',
        handler: () => { deleteMember(member) }
      }
    ]
  })
  await alert.present()
}

const deleteMember = async (member) => {
  deletingId.value = member.id
  try {
    await API.delete(API.SUPPORT_MEMBERSHIP_DETAIL(member.id))
    const toast = await toastController.create({
      message: 'Miembro de soporte eliminado.',
      duration: 3000,
      color: 'success',
      position: 'top'
    })
    await toast.present()
    fetchMembers()
  } catch (err) {
    console.error('Error eliminando miembro de soporte:', err)
    const toast = await toastController.create({
      message: err.message || 'Error al eliminar el miembro de soporte.',
      duration: 4000,
      color: 'danger',
      position: 'top'
    })
    await toast.present()
  } finally {
    deletingId.value = null
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

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-avatar {
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-subtitle {
  margin: 2px 0 0;
  color: var(--ion-color-medium);
  font-size: 0.85rem;
}

.card-details {
  margin-top: 12px;
}

.card-detail-row {
  display: flex;
  gap: 8px;
}

.detail-label {
  color: var(--ion-color-medium);
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
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
</style>