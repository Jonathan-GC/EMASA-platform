<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <!-- Welcome Section -->
      <div v-if="pageReady" class="current-dashboard">
      <div class="welcome-section">
          <div class="gradient-bg"></div>
          <div class="welcome-content">
            <div class="welcome-text">
              <div class="greeting">Bienvenido de vuelta,</div>
              <h1 class="welcome-title">{{ userName }}</h1>
              <div class="user-meta">
                <ion-chip class="role-chip" outline>
                  <ion-icon :icon="icons.person_circle"></ion-icon>
                  <ion-label>{{ userRoleLabel }}</ion-label>
                </ion-chip>
                <ion-chip class="platform-chip" outline>
                  <ion-icon :icon="icons.phone_portrait"></ion-icon>
                  <ion-label>{{ platformLabel }}</ion-label>
                </ion-chip>
              </div>
            </div>
            <div class="status-container">
              <ion-badge :color="systemStatusColor" class="system-badge">
                <ion-icon :icon="icons.checkmark"></ion-icon>
                {{ systemStatus }}
              </ion-badge>
            </div>
          </div>
        </div>
     

      <div class="dashboard-container">
        <!-- Real-Time Metrics -->
        <div class="section metrics-section">
          <div class="section-header">
            <h2 class="section-title">
              <ion-icon :icon="statsChartOutline"></ion-icon>
              Resumen del sistema
            </h2>
            <p class="section-description">datos del sistema en tiempo real</p>
          </div>
          <ion-grid>
            <ion-row>
              <ion-col size="12" size-md="6" size-lg="3" v-for="metric in metrics" :key="metric.title">
                <ion-card class="metric-card">
                  <ion-card-content>
                    <div class="metric-content">
                      <div class="metric-icon" :class="`${metric.color}-bg`">
                        <ion-icon :icon="metric.icon"></ion-icon>
                      </div>
                      <div class="metric-details">
                        <p class="metric-title">{{ metric.title }}</p>
                        <h2 class="metric-value">{{ metric.value }}</h2>
                      </div>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
            </ion-row>
          </ion-grid>
        </div>

        <!-- Quick Navigation & Recent Activity -->
        <ion-grid class="section">
          <ion-row>

            <!-- Recent Activity takes 1/3 on large screens -->
            <ion-col size="12" size-lg="4">
              <div class="subsection">
                <div class="section-header">
                  <h2 class="section-title">
                    <ion-icon :icon="timeOutline"></ion-icon>
                    Recent Activity
                  </h2>
                  <p class="section-description">Latest system events</p>
                </div>
                <ion-card class="activity-card">
                  <ion-list>
                    <ion-item v-for="activity in recentActivity" :key="activity.id" lines="full" class="activity-item">
                      <div class="activity-icon" :class="`${activity.color}-bg`" slot="start">
                        <ion-icon :icon="activity.icon"></ion-icon>
                      </div>
                      <ion-label>
                        <h3>{{ activity.message }}</h3>
                        <p>{{ activity.time }}</p>
                      </ion-label>
                    </ion-item>
                  </ion-list>
                </ion-card>
              </div>
            </ion-col>
          </ion-row>
        </ion-grid>

        <!-- Infrastructure Management -->
        <div class="section" v-if="canAccessInfrastructure">
          <div class="section-header">
            <h2 class="section-title">
              <ion-icon :icon="serverOutline"></ion-icon>
              Infrastructure
            </h2>
            <p class="section-description">Manage your IoT infrastructure</p>
          </div>
          <ion-grid>
            <ion-row>
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/infrastructure/gateways')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container info-bg">
                        <ion-icon :icon="icons.wifi" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Gateways</h3>
                        <p>Administra tus gateways</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/infrastructure/applications')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container tertiary-bg">
                        <ion-icon :icon="icons.package" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Servicios</h3>
                        <p>Mira y configura tus servicios</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/infrastructure/machines')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container medium-bg">
                        <ion-icon :icon="icons.settings" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Máquinas</h3>
                        <p>Gestióna tus máquinas</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
            </ion-row>
          </ion-grid>
        </div>

        <!-- Management Section -->
        <div class="section" v-if="canAccessManagement">
          <div class="section-header">
            <h2 class="section-title">
              <ion-icon :icon="peopleOutline"></ion-icon>
              Management
            </h2>
            <p class="section-description">User and workspace administration</p>
          </div>
          <ion-grid>
            <ion-row>
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/users')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container warning-bg">
                        <ion-icon :icon="icons.people" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Usuarios</h3>
                        <p>Gestión de usuarios</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/workspaces')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container secondary-bg">
                        <ion-icon :icon="icons.layers" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Workspaces</h3>
                        <p>Gestiona tus espacios de trabajo</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessTenants">
                <ion-card class="nav-card" button @click="navigateTo('/tenants')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container tertiary-bg">
                        <ion-icon :icon="icons.building" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Clientes</h3>
                        <p>Administración de clientes</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
            </ion-row>
          </ion-grid>
        </div>

        <!-- Communication -->
        <div class="section">
          <div class="section-header">
            <h2 class="section-title">
              <ion-icon :icon="mailOutline"></ion-icon>
              Communication
            </h2>
            <p class="section-description">Notifications, messages, and support</p>
          </div>
          <ion-grid>
            <ion-row>
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/notifications')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container danger-bg">
                        <ion-icon :icon="icons.notifications" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Notificationes</h3>
                        <p>Ver alertas del sistema</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/inbox')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container info-bg">
                        <ion-icon :icon="icons.mail" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Inbox</h3>
                        <p>Mensajes y actualizaciones</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
              
              <ion-col size="12" size-md="6" size-lg="4">
                <ion-card class="nav-card" button @click="navigateTo('/support')">
                  <ion-card-content>
                    <div class="nav-card-content">
                      <div class="icon-container success-bg">
                        <ion-icon :icon="icons.helpBuoy" size="large"></ion-icon>
                      </div>
                      <div class="nav-card-text">
                        <h3>Soporte</h3>
                        <p>Obtén ayuda y asistencia</p>
                      </div>
                      <ion-icon :icon="chevronForwardOutline" class="nav-arrow"></ion-icon>
                    </div>
                  </ion-card-content>
                </ion-card>
              </ion-col>
            </ion-row>
          </ion-grid>
        </div>
      </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, watch } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { useNotifications } from '@/composables/useNotifications.js'
import API from '@/utils/api/api.js'

import { isPlatform} from '@ionic/vue'

import { Capacitor } from '@capacitor/core'

const router = useRouter()
const authStore = useAuthStore()
const icons = inject('icons', {})
const { notifications, connectionStatus, isConnected, connect, disconnect } = useNotifications()

// Track if component is mounted to prevent updates during transitions
const isMounted = ref(false)
const pageReady = ref(false)
// User information
const userName = computed(() => authStore.user?.username || 'User')
const userRoleLabel = computed(() => {
  const user = authStore.user
  if (user?.is_superuser) return 'Super Administrator'
  if (user?.is_global) return 'Global Administrator'
  if (user?.is_tenant_admin) return 'Tenant Administrator'
  if (user?.role_type === 'manager') return 'Manager'
  if (user?.role_type === 'technician') return 'Technician'
  if (user?.role_type === 'viewer') return 'Viewer'
  return 'User'
})

// Platform information
const platformLabel = computed(() => {
  const platform = Capacitor.getPlatform()
  if (platform === 'web') return isPlatform('mobile') ? 'Mobile Web' : 'Desktop Web'
  if (platform === 'android') return 'Android'
  if (platform === 'ios') return 'iOS'
  return 'Unknown Platform'
})

// System status based on notification connection
const systemStatus = computed(() => {
  if (connectionStatus.value === 'connected') return 'All Systems Operational'
  if (connectionStatus.value === 'connecting') return 'Connecting...'
  return 'Connection Lost'
})

const systemStatusColor = computed(() => {
  if (connectionStatus.value === 'connected') return 'success'
  if (connectionStatus.value === 'connecting') return 'warning'
  return 'danger'
})

// Real-time metrics from API
const metrics = ref([
  {
    title: 'Active Devices',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'info'
  },
  {
    title: 'Gateways',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'success'
  },
  {
    title: 'Tenants',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'warning'
  },
  {
    title: 'Total Users',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'error'
  }
])

// Recent activity from notifications
const recentActivity = computed(() => {
  return notifications.value.slice(0, 5).map((notif, index) => ({
    id: index,
    type: notif.type || 'info',
    message: notif.message || notif.title || 'No message',
    time: formatTime(notif.timestamp),
    icon: getIconForNotificationType(notif.type),
    color: getColorForNotificationType(notif.type)
  }))
})

// Helper functions
function formatTime(timestamp) {
  if (!timestamp) return 'Just now'
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
}

function getIconForNotificationType(type) {
  const iconMap = {
    'error': warningOutline,
    'warning': warningOutline,
    'success': checkmarkCircleOutline,
    'info': notificationsOutline,
    'alert': warningOutline
  }
  return iconMap[type] || notificationsOutline
}

function getColorForNotificationType(type) {
  const colorMap = {
    'error': 'danger',
    'warning': 'warning',
    'success': 'success',
    'info': 'info',
    'alert': 'danger'
  }
  return colorMap[type] || 'primary'
}

// Fetch real metrics from API
async function fetchMetrics() {
  try {
    // Fetch all data in parallel for better performance
    const [devicesResponse, gatewaysResponse, tenantsResponse, usersResponse] = await Promise.all([
      API.get(API.DEVICE),
      API.get(API.GATEWAY),
      API.get(API.TENANT),
      API.get(API.USER)
    ])
    
    // Calculate device counts
    const deviceCount = Array.isArray(devicesResponse) ? devicesResponse.length : devicesResponse?.count || 0
    const activeDevices = Array.isArray(devicesResponse) 
      ? devicesResponse.filter(d => d.is_active || d.status === 'active').length 
      : deviceCount
    
    // Calculate gateway count
    const gatewayCount = Array.isArray(gatewaysResponse) ? gatewaysResponse.length : gatewaysResponse?.count || 0
    
    // Calculate tenant count
    const tenantCount = Array.isArray(tenantsResponse) ? tenantsResponse.length : tenantsResponse?.count || 0
    
    // Calculate user count
    const userCount = Array.isArray(usersResponse) ? usersResponse.length : usersResponse?.count || 0
    
    // Update metrics
    metrics.value = [
      {
        title: 'Active Devices',
        value: activeDevices.toString(),
        change: `${deviceCount} total`,
        trend: activeDevices > 0 ? 'up' : 'neutral',
        icon: icons.antenna,
        color: 'info'
      },
      {
        title: 'Gateways',
        value: gatewayCount.toString(),
        change: 'Connected',
        trend: gatewayCount > 0 ? 'up' : 'neutral',
        icon: icons.wifi,
        color: 'success'
      },
      {
        title: 'Tenants',
        value: tenantCount.toString(),
        change: 'Organizations',
        trend: tenantCount > 0 ? 'up' : 'neutral',
        icon: icons.business,
        color: 'warning'
      },
      {
        title: 'Total Users',
        value: userCount.toString(),
        change: 'Registered',
        trend: userCount > 0 ? 'up' : 'neutral',
        icon: icons.people,
        color: 'danger'
      }
    ]
  } catch (error) {
    console.error('Error fetching metrics:', error)
  }
}

// Permission-based visibility
const canAccessInfrastructure = computed(() => {
  return authStore.isSuperUser || authStore.isGlobalUser || authStore.user?.is_tenant_admin
})

const canAccessManagement = computed(() => {
  return authStore.isSuperUser || authStore.isGlobalUser || authStore.user?.is_tenant_admin
})

const canAccessTenants = computed(() => {
  return authStore.isSuperUser || authStore.isGlobalUser
})

// Navigation
const navigateTo = (path) => {
  router.push(path)
}

onMounted(async () => {
  isMounted.value = true
  pageReady.value = true
  
  // Connect to notification WebSocket
  connect()
  
  // Fetch real metrics
  await fetchMetrics()
  
  // Refresh metrics every 30 seconds
  const metricsInterval = setInterval(() => {
    if (isMounted.value) {
      fetchMetrics()
    }
  }, 30000)
  
  // Cleanup on unmount
  onUnmounted(() => {
    isMounted.value = false
    clearInterval(metricsInterval)
    disconnect()
  })
})

// Cleanup before route leave to prevent visual overlap
onBeforeRouteLeave(() => {
  isMounted.value = false
})
</script>

<style scoped>
ion-page {
  background: var(--ion-background-color, #f4f5f8);
}

ion-content {
  --background: var(--ion-background-color, #f4f5f8);
}

.dashboard-container {
  padding: 0;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

/* Welcome Section with Gradient */
.welcome-section {
  position: relative;
  width: 100%;
  padding: 32px 0;
  margin-bottom: 24px;
  overflow: hidden;
}

.gradient-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--ion-color-orange-500);
  z-index: 0;
  transform: translateZ(0);
  backface-visibility: hidden;
}

.welcome-content {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  flex-wrap: wrap;
}

.welcome-text {
  flex: 1;
  min-width: 250px;
}

.greeting {
  font-size: 16px;
  font-weight: 500;
  color: var(--ion-color-medium);
  margin-bottom: 4px;
  letter-spacing: 0.3px;
}

.welcome-title {
  margin: 0 0 16px 0;
  font-size: 36px;
  font-weight: 700;
  color: var(--ion-text-color);
  line-height: 1.2;
}

.user-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.role-chip,
.platform-chip {
  --background: transparent;
  --color: var(--ion-color-medium);
  border: 1.5px solid var(--ion-color-light);
  font-size: 13px;
  height: 32px;
}

.role-chip ion-icon,
.platform-chip ion-icon {
  font-size: 18px;
  margin-right: 4px;
}

.status-container {
  display: flex;
  align-items: flex-start;
}

.system-badge {
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

/* Connected state - matches ConnectionStatus */
.system-badge[color="success"] {
  background: #d1fae5 !important;
  color: #738e80 !important;
}

/* Disconnected/Warning state - matches ConnectionStatus */
.system-badge[color="danger"],
.system-badge[color="warning"] {
  background: #fee2e2 !important;
  color: #ef4444 !important;
}

/* Pulse animation for non-operational states */


.system-badge[color="danger"],
.system-badge[color="warning"] {
  animation: pulse 3s ease-in-out infinite;
  will-change: opacity;
}

.system-badge ion-icon {
  font-size: 18px;
}

/* Section Styling */
.section {
  margin-bottom: 40px;
  padding: 0 20px;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--ion-text-color);
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title ion-icon {
  font-size: 26px;
  color: var(--ion-color-primary);
}

.section-description {
  margin: 6px 0 0 38px;
  font-size: 14px;
  color: var(--ion-color-medium);
  font-weight: 400;
}

/* Enhanced Navigation Cards */
.nav-card {
  margin: 0;
  cursor: pointer;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  will-change: transform;
  transform: translateZ(0);
}

.nav-card:hover {
  transform: translate3d(0, -4px, 0);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.nav-card:active {
  transform: translate3d(0, -2px, 0);
}

.nav-card ion-card-content {
  padding: 24px;
}

.nav-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Icon Containers with Colored Backgrounds */
.icon-container {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.25s ease;
  will-change: transform;
}

.nav-card:hover .icon-container {
  transform: scale(1.05) rotate(3deg);
}

.icon-container ion-icon {
  font-size: 28px;
}

.warning-bg {
  background: linear-gradient(135deg, rgba(255, 140, 9, 0.15), rgba(255, 140, 9, 0.25));
  color: var(--ion-color-warning);
}

.danger-bg {
  background: linear-gradient(135deg, rgba(235, 68, 90, 0.15), rgba(235, 68, 90, 0.25));
  color: var(--ion-color-danger);
}

.success-bg {
  background: linear-gradient(135deg, rgba(16, 220, 96, 0.15), rgba(16, 220, 96, 0.25));
  color: var(--ion-color-success);
}

.info-bg {
  background: linear-gradient(135deg, rgba(56, 128, 255, 0.15), rgba(56, 128, 255, 0.25));
  color: var(--ion-color-info);
}

.secondary-bg {
  background: linear-gradient(135deg, rgba(12, 209, 232, 0.15), rgba(12, 209, 232, 0.25));
  color: var(--ion-color-cyan-500);
}

.tertiary-bg {
  background: linear-gradient(135deg, rgba(112, 68, 255, 0.15), rgba(112, 68, 255, 0.25));
  color: var(--ion-color-tertiary);
}

.medium-bg {
  background: linear-gradient(135deg, rgba(146, 148, 151, 0.15), rgba(146, 148, 151, 0.25));
  color: var(--ion-color-medium);
}

.nav-card-text {
  flex: 1;
  min-width: 0;
}

.nav-card-text h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--ion-text-color);
  letter-spacing: -0.2px;
}

.nav-card-text p {
  margin: 0;
  font-size: 14px;
  color: var(--ion-color-medium);
  line-height: 1.4;
  font-weight: 400;
}

.nav-arrow {
  color: var(--ion-color-light);
  flex-shrink: 0;
  font-size: 24px;
  transition: transform 0.3s ease;
}

.nav-card:hover .nav-arrow {
  transform: translateX(4px);
  color: var(--ion-color-medium);
}

/* Subsection for nested sections */
.subsection {
  margin-bottom: 32px;
}

/* Metrics Section */
.metrics-section {
  margin-bottom: 32px;
}

.metric-card {
  margin: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.metric-card ion-card-content {
  padding: 20px;
}

.metric-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon ion-icon {
  font-size: 24px;
}

.metric-details {
  flex: 1;
  min-width: 0;
}

.metric-title {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--ion-color-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--ion-text-color);
  line-height: 1;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.metric-change ion-icon {
  font-size: 16px;
}

.change-up {
  color: var(--ion-color-success);
}

.change-down {
  color: var(--ion-color-danger);
}

.change-neutral {
  color: var(--ion-color-medium);
}

/* Activity Card */
.activity-card {
  margin: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 100%;
}

.activity-card ion-list {
  background: transparent;
  padding: 0;
}

.activity-item {
  --padding-start: 16px;
  --padding-end: 16px;
  --inner-padding-end: 0;
  --min-height: 72px;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-icon ion-icon {
  font-size: 20px;
}

.activity-item ion-label h3 {
  font-size: 14px;
  font-weight: 500;
  color: var(--ion-text-color);
  margin-bottom: 4px;
}

.activity-item ion-label p {
  font-size: 12px;
  color: var(--ion-color-medium);
}

/* Color backgrounds for metrics and activity icons */
.primary-bg {
  background: linear-gradient(135deg, rgba(56, 128, 255, 0.15), rgba(56, 128, 255, 0.25));
  color: var(--ion-color-primary);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .welcome-section {
    padding: 24px 0;
  }

  .welcome-content {
    padding: 0 16px;
  }

  .greeting {
    font-size: 14px;
  }

  .welcome-title {
    font-size: 28px;
  }

  .section {
    padding: 0 16px;
    margin-bottom: 32px;
  }

  .section-title {
    font-size: 20px;
  }

  .section-title ion-icon {
    font-size: 24px;
  }

  .section-description {
    font-size: 13px;
    margin-left: 36px;
  }

  .nav-card ion-card-content {
    padding: 20px;
  }

  .icon-container {
    width: 48px;
    height: 48px;
  }

  .icon-container ion-icon {
    font-size: 24px;
  }

  .nav-card-text h3 {
    font-size: 16px;
  }

  .nav-card-text p {
    font-size: 13px;
  }

  .role-chip,
  .platform-chip {
    font-size: 12px;
    height: 28px;
  }

  .metric-card ion-card-content {
    padding: 16px;
  }

  .metric-value {
    font-size: 24px;
  }

  .metric-title {
    font-size: 12px;
  }

  .metric-change {
    font-size: 11px;
  }

  .activity-item {
    --min-height: 64px;
  }

  .activity-icon {
    width: 36px;
    height: 36px;
  }

  .activity-icon ion-icon {
    font-size: 18px;
  }
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
  .nav-card {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .nav-card:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  }

  .gradient-bg {
    opacity: 0.08;
  }

  .role-chip,
  .platform-chip {
    border-color: var(--ion-color-dark);
  }
}
</style>
