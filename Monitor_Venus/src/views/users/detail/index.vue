<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div v-if="!loading && userData" class="current-dashboard">
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon :icon="icons.person"></ion-icon>
              Usuario
            </h1>
          </div>
        </div>
        <div class="page-layout">
          <!-- Left Sidebar -->
          <aside class="sidebar">
            <!-- Profile Card -->
            <div class="profile-card">
              <QuickActions v-if="isOwnProfile" class="profile-edit-action" type="user" :index="userData.id"
                :name="userData.username" to-edit :initial-data="sidebarInitialData" @item-edited="handleItemUpdated" />
              <UserAvatar size="large" :name="fullName" :profile-image="avatarSrc" :show-name="false" :show-role="false"
                :clickable="false" :show-tenant-badge="false" />
              <h2 class="profile-name">{{ fullName }}</h2>
              <p v-if="userData.tenant_name" class="profile-tenant">{{ userData.tenant_name }}</p>
            </div>

            <!-- Details Card -->
            <div class="details-card">
              <div class="detail-row">
                <span class="detail-label">Usuario</span>
                <span class="detail-value">@{{ userData.username }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Email</span>
                <span class="detail-value">{{ userData.email || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Estado</span>
                <ion-chip :color="userData.is_active ? 'success' : 'danger'" size="small" class="detail-chip">
                  {{ userData.is_active ? 'Activo' : 'Suspendido' }}
                </ion-chip>
              </div>
              <div class="detail-row">
                <span class="detail-label">Rol</span>
                <div v-if="userRoles.length" class="role-chips">
                  <ion-chip v-for="role in userRoles" :key="role.id || role.name" size="small" class="role-chip"
                    :style="roleChipStyle(role)">
                    {{ role.name }}
                  </ion-chip>
                </div>
                <span v-else class="detail-value">-</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Código Fiscal</span>
                <span class="detail-value code-value">{{ userData.code || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Contacto</span>
                <span class="detail-value">{{ formatContact }}</span>
              </div>
              <div v-if="userData.country" class="detail-row">
                <span class="detail-label">País</span>
                <span class="detail-value">{{ userData.country }}</span>
              </div>
            </div>
          </aside>

          <!-- Main Content -->
          <main class="main-content">
            <!-- Tabs -->
            <div class="tabs-bar">
              <button class="tab-btn" :class="{ active: selectedTab === 'overview' }" @click="selectedTab = 'overview'">
                <ion-icon :icon="icons.time"></ion-icon>
                Resumen
              </button>
              <button class="tab-btn" :class="{ active: selectedTab === 'teams' }" @click="selectedTab = 'teams'">
                <ion-icon :icon="icons.people"></ion-icon>
                Equipos
              </button>
              <button v-if="isOwnProfile" class="tab-btn" :class="{ active: selectedTab === 'connections' }"
                @click="selectedTab = 'connections'">
                <ion-icon :icon="icons.link"></ion-icon>
                Conexiones
              </button>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
              <!-- Overview Tab -->
              <div v-if="selectedTab === 'overview'" class="tab-panel">
                <div class="content-card">
                  <h3 class="content-card-title">
                    <ion-icon :icon="icons.time"></ion-icon>
                    Línea de Actividad
                  </h3>
                  <div class="activity-placeholder">
                    <ion-icon :icon="icons.time" size="large" color="medium"></ion-icon>
                    <p>No hay actividad reciente para mostrar.</p>
                    <span class="placeholder-hint">Los registros de auditoría aparecerán aquí.</span>
                  </div>
                </div>
              </div>

              <!-- Teams Tab -->
              <div v-if="selectedTab === 'teams'" class="tab-panel">
                <div class="content-card">
                  <h3 class="content-card-title">
                    <ion-icon :icon="icons.people"></ion-icon>
                    Equipos y Roles
                  </h3>

                  <div v-if="teamsLoading" class="teams-state">
                    <ion-spinner name="crescent"></ion-spinner>
                    <p>Cargando equipos...</p>
                  </div>

                  <div v-else-if="teamsError" class="teams-state">
                    <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
                    <p>{{ teamsError }}</p>
                    <ion-button @click="fetchTeams" fill="outline" color="primary">Reintentar</ion-button>
                  </div>

                  <div v-else-if="teams.length" class="teams-grid">
                    <div v-for="team in teams" :key="team.role.id || team.role.name" class="team-card"
                      :style="{ '--role-color': team.role.color || '#5865F2' }" @click="openTeamModal(team.role)">
                      <div class="team-card-header">
                        <h4 class="team-role-name">{{ team.role.name }}</h4>
                        <div v-if="team.role.color" class="team-color-dot"
                          :style="{ backgroundColor: team.role.color }"></div>
                      </div>
                      <p class="team-role-description">{{ team.role.description || 'Sin descripción' }}</p>
                      <div class="team-members">
                        <div class="avatar-stack">
                          <div v-for="member in team.members.slice(0, 3)" :key="member.id" class="avatar-circle">
                            <img v-if="memberAvatarSrc(member.img)" :src="memberAvatarSrc(member.img)"
                              :alt="memberFullName(member)" />
                            <div v-else class="avatar-initials" :style="{ backgroundColor: memberColor(member) }">
                              {{ memberInitials(member) }}
                            </div>
                          </div>
                          <div v-if="team.members.length > 3" class="avatar-circle more-circle">
                            +{{ team.members.length - 3 }}
                          </div>
                        </div>
                        <span class="team-member-count">
                          <ion-icon :icon="icons.people"></ion-icon>
                          {{ team.members.length }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div v-else class="teams-state">
                    <ion-icon :icon="icons.people" size="large" color="medium"></ion-icon>
                    <p>El usuario no tiene roles asignados.</p>
                  </div>
                </div>
              </div>

              <!-- Connections Tab -->
              <div v-if="isOwnProfile && selectedTab === 'connections'" class="tab-panel">
                <div class="content-card">
                  <h3 class="content-card-title">
                    <ion-icon :icon="icons.link"></ion-icon>
                    Conexiones Disponibles
                  </h3>
                  <div class="connection-list">
                    <div class="connection-item">
                      <div class="connection-info">
                        <svg viewBox="0 0 48 48" width="24" height="24" aria-hidden="true">
                          <path fill="#EA4335"
                            d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
                          <path fill="#4285F4"
                            d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
                          <path fill="#FBBC05"
                            d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
                          <path fill="#34A853"
                            d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
                        </svg>
                        <div class="connection-text">
                          <span class="connection-name">Google</span>
                          <ion-chip v-if="hasGoogleLinked" color="success" size="small" class="google-email-chip">
                            {{ googleEmail }}
                          </ion-chip>
                        </div>
                      </div>
                      <div class="connection-toggle">
                        <ion-toggle :checked="googleToggleEnabled" @ionChange="handleGoogleToggle"
                          :disabled="googleToggleLoading"></ion-toggle>
                      </div>
                    </div>
                  </div>
                  <p v-if="linkError" class="link-error">{{ linkError }}</p>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>

      <div v-else-if="loading" class="page-loading">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando información del usuario...</p>
      </div>

      <div v-else class="page-loading">
        <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
        <p>{{ error || 'No se pudo cargar la información del usuario.' }}</p>
        <ion-button @click="fetchUser" fill="outline" color="primary">
          Reintentar
        </ion-button>
      </div>
    </ion-content>

    <!-- Google Link Modal -->
    <ion-modal :is-open="isLinkModalOpen" @did-dismiss="handleLinkModalDismiss" class="google-link-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Vincular Google</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeLinkModal">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <div class="google-link-modal-content">
        <svg viewBox="0 0 48 48" width="48" height="48" aria-hidden="true">
          <path fill="#EA4335"
            d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
          <path fill="#4285F4"
            d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
          <path fill="#FBBC05"
            d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
          <path fill="#34A853"
            d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
        </svg>
        <p class="modal-description">
          Vincula tu cuenta de Google para acceder de forma rápida y segura, sin necesidad de contraseña.
        </p>
        <GoogleLoginButton mode="link" :next="`/users/${userId}`" @started="handleLinkStarted" />
      </div>
    </ion-modal>

    <!-- Google Unlink Confirmation Modal -->
    <ion-modal :is-open="isUnlinkModalOpen" @did-dismiss="closeUnlinkModal" class="google-link-modal">
      <ion-header class="custom">
        <ion-toolbar>
          <ion-title>Desvincular Google</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeUnlinkModal">
              <ion-icon :icon="icons.close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <div class="google-link-modal-content">
        <div class="unlink-icon">
          <ion-icon :icon="icons.link" size="large" color="medium"></ion-icon>
        </div>
        <p class="modal-description">
          ¿Seguro que deseas desvincular tu cuenta de Google? Podrás volver a vincularla cuando quieras y
          seguirás accediendo con tu correo y contraseña.
        </p>
        <div class="modal-actions">
          <ion-button fill="outline" @click="closeUnlinkModal">Cancelar</ion-button>
          <ion-button color="danger" :disabled="googleUnlinkLoading" @click="confirmGoogleUnlink">
            <ion-spinner v-if="googleUnlinkLoading" name="crescent" slot="start"></ion-spinner>
            Desvincular
          </ion-button>
        </div>
      </div>
    </ion-modal>
  </ion-page>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { modalController, toastController } from '@ionic/vue'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'
import RoleMembersModal from '@components/forms/roles/RoleMembersModal.vue'

const route = useRoute()
const authStore = useAuthStore()
const icons = inject('icons', {})

const userId = route.params.user_id

const isOwnProfile = computed(() => authStore.currentUserId === userId)

const userData = ref(null)
const loading = ref(true)
const error = ref(null)
const selectedTab = ref('overview')

const googleToggleLoading = ref(false)
const isLinkModalOpen = ref(false)
const isUnlinkModalOpen = ref(false)
const googleUnlinkLoading = ref(false)
const linkError = ref(null)

const fetchUser = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await API.get(API.USER_PROFILE(userId))
    const data = Array.isArray(response) ? response[0] : response
    userData.value = {
      id: data.user_info?.id,
      code: data.user_info?.code,
      username: data.user_info?.username,
      email: data.user_info?.email,
      name: data.user_info?.name,
      last_name: data.user_info?.last_name,
      img: data.user_info?.img,
      is_active: data.status?.is_active,
      phone: data.contact_info?.phone,
      phone_code: data.contact_info?.phone_code,
      country: data.contact_info?.country,
      address: data.contact_info?.address,
      tenant: data.tenant,
      tenant_name: data.tenant?.name,
      roles: data.roles,
    }
  } catch (err) {
    error.value = err.message || 'Error al cargar usuario'
  } finally {
    loading.value = false
  }
}

const fullName = computed(() => {
  if (!userData.value) return ''
  const { name, last_name, username } = userData.value
  if (name && last_name) return `${name} ${last_name}`
  if (name) return name
  return username || ''
})

const avatarSrc = computed(() => {
  const img = userData.value?.img
  if (!img) return null
  if (img.startsWith('http://') || img.startsWith('https://')) return img
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  const imagePath = img.startsWith('/') ? img : `/${img}`
  return `${backendUrl}${imagePath}`
})

const formatContact = computed(() => {
  if (!userData.value) return '-'
  const pc = userData.value.phone_code || ''
  const p = userData.value.phone
  if (p) return `${pc} ${p}`
  return '-'
})

const userRoles = computed(() => {
  const d = userData.value
  if (Array.isArray(d?.roles) && d.roles.length) return d.roles
  if (isOwnProfile.value) return authStore.userRoles
  return []
})

const teams = ref([])
const teamsLoading = ref(false)
const teamsError = ref(null)

const memberAvatarSrc = (img) => {
  if (!img) return null
  if (img.startsWith('http://') || img.startsWith('https://')) return img
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  const imagePath = img.startsWith('/') ? img : `/${img}`
  return `${backendUrl}${imagePath}`
}

const memberFullName = (member) => {
  const parts = [member.name, member.last_name].filter(Boolean)
  return parts.join(' ') || member.username || member.email || 'Usuario'
}

const memberInitials = (member) => {
  const parts = [member.name, member.last_name].filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  const name = parts[0] || member.username || member.email || 'U'
  return name.substring(0, 2).toUpperCase()
}

const memberColor = (member) => {
  const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#6366f1', '#f97316']
  const name = memberFullName(member)
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const fetchTeams = async () => {
  const roles = userRoles.value
  if (!roles.length) {
    teams.value = []
    teamsLoading.value = false
    teamsError.value = null
    return
  }
  teamsLoading.value = true
  teamsError.value = null
  try {
    const results = await Promise.allSettled(
      roles.map(async (role) => {
        const response = await API.get(API.ROLE_MEMBERSHIP(role.id))
        const members = Array.isArray(response) ? response : (response?.data || [])
        return { role, members }
      })
    )
    const loaded = []
    for (const result of results) {
      if (result.status === 'fulfilled') loaded.push(result.value)
    }
    teams.value = loaded
    if (!loaded.length && roles.length) {
      teamsError.value = 'No se pudieron cargar los equipos.'
    }
  } catch (err) {
    teamsError.value = err.message || 'No se pudieron cargar los equipos.'
    teams.value = []
  } finally {
    teamsLoading.value = false
  }
}

watch(userRoles, fetchTeams)

const openTeamModal = async (role) => {
  const modal = await modalController.create({
    component: RoleMembersModal,
    componentProps: { role },
    cssClass: 'full-modal'
  })
  await modal.present()
}

const roleTextColor = (hex) => {
  if (!hex) return undefined
  const c = hex.replace('#', '')
  if (c.length < 6) return undefined
  const r = parseInt(c.substring(0, 2), 16)
  const g = parseInt(c.substring(2, 4), 16)
  const b = parseInt(c.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6 ? '#1f2937' : '#ffffff'
}

const roleChipStyle = (role) => {
  if (!role?.color) return {}
  return {
    'border': role.color ? `1px solid ${role.color}` : undefined,
    '--background': role.color + '80',
    '--color': roleTextColor(role.color),
  }
}

const hasGoogleLinked = computed(() => {
  return authStore.googleLinked
})

const googleToggleEnabled = ref(false)

watch(() => authStore.googleLinked, (linked) => {
  googleToggleEnabled.value = linked
})

const googleEmail = computed(() => authStore.googleEmail || '')

const sidebarInitialData = computed(() => {
  if (!userData.value) return {}
  const d = userData.value
  return {
    code: d.code,
    username: d.username,
    email: d.email,
    name: d.name,
    last_name: d.last_name,
    phone: d.phone,
    phone_code: d.phone_code,
    country: d.country,
    tenant: d.tenant?.id || d.tenant,
    is_active: d.is_active,
    img: d.img,
    address: d.address,
  }
})

const handleItemUpdated = () => {
  fetchUser()
}

const handleGoogleToggle = async (ev) => {
  const checked = ev.detail.checked
  if (checked) {
    googleToggleEnabled.value = true
    if (!hasGoogleLinked.value) {
      isLinkModalOpen.value = true
    }
  } else {
    googleToggleEnabled.value = false
    if (hasGoogleLinked.value) {
      isUnlinkModalOpen.value = true
    }
  }
}

const handleLinkModalDismiss = () => {
  isLinkModalOpen.value = false
  if (!hasGoogleLinked.value) {
    googleToggleEnabled.value = false
  }
}

const closeLinkModal = () => {
  isLinkModalOpen.value = false
  if (!hasGoogleLinked.value) {
    googleToggleEnabled.value = false
  }
}

const handleLinkStarted = () => {
  isLinkModalOpen.value = false
}

const closeUnlinkModal = () => {
  isUnlinkModalOpen.value = false
  googleToggleEnabled.value = authStore.googleLinked
}

const confirmGoogleUnlink = async () => {
  googleUnlinkLoading.value = true
  try {
    await API.post(API.GOOGLE_UNLINK)
    await authStore.fetchUserProfile().catch(() => { })
    googleToggleEnabled.value = authStore.googleLinked
    isUnlinkModalOpen.value = false
  } catch (err) {
    console.error('Error al desvincular Google:', err)
    googleToggleEnabled.value = true
    const toast = await toastController.create({
      message: 'No se pudo desvincular la cuenta de Google. Inténtalo de nuevo.',
      duration: 4000,
      color: 'danger',
      position: 'top'
    })
    await toast.present()
  } finally {
    googleUnlinkLoading.value = false
  }
}

const refreshOwnProfile = () => {
  if (!isOwnProfile.value) return
  authStore.fetchUserProfile().catch(() => { })
  googleToggleEnabled.value = authStore.googleLinked
}

onMounted(() => {
  fetchUser()
  refreshOwnProfile()
  window.addEventListener('google-account-linked', handleLinked)
  window.addEventListener('google-account-linked-error', handleLinkError)
})

onBeforeUnmount(() => {
  window.removeEventListener('google-account-linked', handleLinked)
  window.removeEventListener('google-account-linked-error', handleLinkError)
})

const handleLinked = () => {
  linkError.value = null
  fetchUser()
  refreshOwnProfile()
}

const handleLinkError = (ev) => {
  linkError.value = ev?.detail?.message || 'No se pudo vincular la cuenta de Google.'
  fetchUser()
  refreshOwnProfile()
}
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.header {
  margin-bottom: 30px;
}

.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ion-text-color);
}

.page-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* ── Sidebar ── */
.sidebar {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 20px;
}

.profile-card {
  position: relative;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 32px 24px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.profile-edit-action {
  position: absolute;
  top: 8px;
  right: 8px;
}

.profile-card :deep(.user-avatar-container) {
  justify-content: center;
  padding: 0;
  width: auto;
}

.profile-name {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--ion-text-color);
  text-align: center;
}

.profile-tenant {
  margin: 0;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  text-align: center;
}

.details-card {
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex-shrink: 0;
  margin-right: 12px;
}

.detail-value {
  font-size: 0.9rem;
  color: var(--ion-text-color);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.code-value {
  font-family: monospace;
  font-size: 0.85rem;
}

.detail-chip {
  margin: 0;
  height: 22px;
  font-size: 0.75rem;
}

.role-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.role-chip {
  margin: 0;
  height: 22px;
  font-size: 0.75rem;
}

.sidebar-actions {
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: center;
}

/* ── Main Content ── */
.main-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tabs-bar {
  display: flex;
  gap: 4px;
  border-radius: 12px;
  padding: 4px;
  flex-wrap: nowrap;
  overflow-x: auto;
  scrollbar-width: none;
}

.tabs-bar::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--ion-color-medium);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  background: var(--ion-color-light-tint, #f9fafb);
}

.tab-btn.active {
  background: var(--ion-color-primary);
  color: white;
}

.tab-btn ion-icon {
  font-size: 1.1rem;
}

.tab-content {
  flex: 1;
}

.content-card {
  box-sizing: border-box;
  width: 100%;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.content-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--ion-text-color);
}

.activity-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.activity-placeholder p {
  margin: 0;
  font-size: 0.95rem;
}

.placeholder-hint {
  font-size: 0.8rem;
  opacity: 0.7;
}

/* ── Teams Tab ── */
.teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.team-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: var(--ion-card-background, #fff);
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-top: 3px solid var(--role-color, #5865F2);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.team-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.team-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.team-role-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ion-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.team-role-description {
  margin: 0;
  font-size: 0.82rem;
  color: var(--ion-color-medium);
  line-height: 1.4;
  min-height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.team-members {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
}

.avatar-stack {
  display: flex;
  align-items: center;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid var(--ion-card-background, #fff);
  margin-left: -10px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.avatar-circle:first-child {
  margin-left: 0;
}

.avatar-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-initials {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
}

.more-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ion-color-medium);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
}

.team-member-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.teams-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.teams-state p {
  margin: 0;
  font-size: 0.9rem;
}

/* ── Connections Tab ── */
.connection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.connection-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 8px;
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.connection-name {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ion-text-color);
}

.google-email-chip {
  align-self: flex-start;
  margin: 4px 0 0;
}

.connection-toggle {
  flex-shrink: 0;
}

.link-error {
  color: #c0392b;
  font-size: 0.9rem;
  margin: 10px 0 0;
}

/* ── Google Link Modal ── */
.google-link-modal {
  --width: 340px;
  --height: auto;
  --max-height: 90vh;
  --border-radius: 16px;
}

.google-link-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 200px;
  padding: 24px 32px 32px;
  text-align: center;
}

.modal-description {
  margin: 0;
  font-size: 0.95rem;
  color: var(--ion-color-medium);
  line-height: 1.5;
  max-width: 280px;
}

.unlink-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--ion-color-light, #f3f4f6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 8px;
}

/* ── Loading & Error ── */
.page-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 60vh;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .current-dashboard {
    padding: 12px;
  }

  .page-container {
    padding: 12px;
  }

  .page-layout {
    flex-direction: column;
    padding-inline: 16px;
  }

  .sidebar {
    width: 100%;
    position: static;
  }

  .main-content {
    width: 100%;
  }

  .profile-card {
    padding: 20px;
  }

  .details-card {
    padding: 12px 16px;
  }

  .tabs-bar {
    overflow-x: auto;
  }

  .tab-btn {
    flex: 0 0 auto;
    padding: 8px 12px;
    font-size: 0.85rem;
    white-space: nowrap;
  }

  .content-card {
    padding: 16px;
  }
}
</style>
