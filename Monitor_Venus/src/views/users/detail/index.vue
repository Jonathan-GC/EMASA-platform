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
            <UserProfileCard :user="userData" :is-own-profile="isOwnProfile" @edited="fetchUser" />
            <UserDetailsCard :user="userData" :roles="userRoles" />
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
              <UserOverviewTab v-if="selectedTab === 'overview'" :user-id="userId" />
              <UserTeamsTab v-if="selectedTab === 'teams'" :roles="userRoles" />
              <UserConnectionsTab v-if="isOwnProfile && selectedTab === 'connections'" :user-id="userId" />
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
  </ion-page>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import API from '@/utils/api/api'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const authStore = useAuthStore()
const icons = inject('icons', {})

const userId = route.params.user_id

const isOwnProfile = computed(() => authStore.currentUserId === userId)

const userData = ref(null)
const loading = ref(true)
const error = ref(null)
const selectedTab = ref('overview')

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

const userRoles = computed(() => {
  const d = userData.value
  if (Array.isArray(d?.roles) && d.roles.length) return d.roles
  if (isOwnProfile.value) return authStore.userRoles
  return []
})

onMounted(() => {
  fetchUser()
})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.header {
  margin-bottom: 30px;
}

.page-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.sidebar {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 20px;
}

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

@media (max-width: 768px) {
  .current-dashboard {
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

  .tabs-bar {
    overflow-x: auto;
  }

  .tab-btn {
    flex: 0 0 auto;
    padding: 8px 12px;
    font-size: 0.85rem;
    white-space: nowrap;
  }
}
</style>
