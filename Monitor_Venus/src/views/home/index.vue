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
              <ion-col size="12" size-md="6" size-lg="3" v-for="metric in visibleMetrics" :key="metric.title">
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

        <!-- Last Activity Table -->
        <div class="section" v-if="canAccessManagement">
          <div class="section-header">
            <h2 class="section-title">
              <ion-icon :icon="icons.list"></ion-icon>
              Resumen de Auditoría
            </h2>
            <p class="section-description">Los últimos 5 movimientos procesados en el sistema</p>
          </div>
          <ion-card class="table-card">
            <div class="table-wrapper">
              <ion-grid class="data-table">
                <ion-row class="table-header">
                  <ion-col size="1.2">Acción</ion-col>
                  <ion-col size="1.2">Entidad</ion-col>
                  <ion-col size="2.5">Recurso</ion-col>
                  <ion-col size="3.1">Cambios Realizados</ion-col>
                  <ion-col size="2">Autor</ion-col>
                  <ion-col size="2">Fecha</ion-col>
                </ion-row>
                
                <ion-row v-for="item in activityTable" :key="item.id" class="table-row-stylized">
                  <ion-col size="1.2">
                    <ion-chip :color="item.color" class="action-chip">
                      <ion-label>{{ item.actionLabel }}</ion-label>
                    </ion-chip>
                  </ion-col>
                  <ion-col size="1.2">
                    <ion-chip outline class="entity-chip">
                      <ion-label>{{ item.entity }}</ion-label>
                    </ion-chip>
                  </ion-col>
                  <ion-col size="2.5">
                    <div class="user-info">
                      <strong class="truncate">{{ item.object_repr }}</strong>
                    </div>
                  </ion-col>
                  <ion-col size="3.1">
                    <span class="change-log">{{ item.changes }}</span>
                  </ion-col>
                  <ion-col size="2">
                    <div class="actor-info">
                      <ion-icon :icon="icons.person" class="actor-icon"></ion-icon>
                      <span class="user-username">{{ item.actor }}</span>
                    </div>
                  </ion-col>
                  <ion-col size="2">
                    <span class="user-email">{{ item.time }}</span>
                  </ion-col>
                </ion-row>

                <div v-if="activityTable.length === 0" class="empty-state">
                  <ion-icon :icon="icons.archive" class="empty-icon"></ion-icon>
                  <p>No se encontró actividad reciente en el sistema.</p>
                </div>
              </ion-grid>
            </div>
          </ion-card>
        </div>

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
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessGateways">
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
              
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessApplications">
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
              
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessMachines">
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
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessUsers">
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
              
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessWorkspaces">
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
              
              <ion-col size="12" size-md="6" size-lg="4" v-if="canAccessInbox">
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

import { statsChartOutline, timeOutline, serverOutline, peopleOutline, mailOutline, chevronForwardOutline, createOutline, addOutline, trashOutline, refreshOutline, informationCircleOutline } from 'ionicons/icons'

const router = useRouter()
const authStore = useAuthStore()
const icons = inject('icons', {})
const { connectionStatus, connect, disconnect } = useNotifications()

// Recent Activity from API (Audit logs)
const serverActivity = ref([])
const actorDetails = ref({}) // Cache for actor names { id: name }

const activityTable = computed(() => {
  return serverActivity.value.map(item => ({
    id: item.id,
    message: formatActivityMessage(item),
    time: formatTime(item.timestamp),
    icon: getActivityIcon(item),
    color: getActivityColor(item),
    actionLabel: getActionLabel(item),
    object_repr: cleanObjectRepr(item.object_repr),
    actor: actorDetails.value[item.actor] || 'Cargando...',
    entity: item.model ? item.model.charAt(0).toUpperCase() + item.model.slice(1) : 'General',
    changes: formatChanges(item.changes),
    timestamp: item.timestamp
  }))
})

function cleanObjectRepr(repr) {
  if (!repr) return ''
  // If it's something like "Activation object (10)" or "Activation object 10", simplify it
  // This matches "Something object (Anything)" or "Something object Anything"
  const match = repr.match(/.*object\s*\(?([^)]+)\)?/i)
  if (match && match[1]) {
    return match[1].trim()
  }
  return repr.trim()
}

function formatChanges(changes) {
  if (!changes || Object.keys(changes).length === 0) return 'Sin cambios detectados'
  
  const entries = Object.entries(changes)
  if (entries.length === 0) return 'Sin cambios detectados'

  const formatValue = (val) => {
    if (val === 'None' || val === null || val === undefined) return 'vacío'
    if (typeof val === 'object' && val !== null) {
      return val.id || val.name || JSON.stringify(val)
    }
    return val
  }

  return entries.slice(0, 2).map(([key, value]) => {
    // Clean up key
    const field = key.replace(/_/g, ' ')
    const oldValue = formatValue(value[0])
    const newValue = formatValue(value[1])
    
    // Friendly language based on context
    if (oldValue === 'vacío') return `Nuevo ${field}: "${newValue}"`
    return `Cambió ${field} de "${oldValue}" a "${newValue}"`
  }).join(' | ') + (entries.length > 2 ? ' ...' : '')
}

function getActionLabel(item) {
  const actionMap = {
    '0': 'Creado',
    '1': 'Editado',
    '2': 'Borrado'
  }
  return actionMap[item.action] || 'Evento'
}

function formatActivityMessage(item) {
  const actionMap = {
    '0': 'Creación',
    '1': 'Actualización',
    '2': 'Eliminación'
  }
  const action = actionMap[item.action] || 'Evento'
  const resource = cleanObjectRepr(item.object_repr)
  return `${action}: ${resource}`
}

function getActivityIcon(item) {
  const actionIconMap = {
    '1': createOutline, // Updated
    '0': addOutline,    // Created
    '2': trashOutline   // Deleted
  }
  return actionIconMap[item.action] || informationCircleOutline
}

function getActivityColor(item) {
  const actionColorMap = {
    '1': 'warning', // Updated
    '0': 'success', // Created
    '2': 'danger'   // Deleted
  }
  return actionColorMap[item.action] || 'primary'
}

// Fetch Activity Logs
async function fetchActivity() {
  try {
    const endpoint = authStore.isSuperUser ? API.AUDIT : API.TENANT_AUDIT
    const response = await API.get(endpoint)
    const logs = Array.isArray(response) ? response : (response?.results || [])
    serverActivity.value = logs.slice(0, 5) // Get exactly last 5

    // Fetch actor full names for the logs
    const uniqueActors = [...new Set(serverActivity.value.map(log => log.actor).filter(id => id && !actorDetails.value[id]))]
    
    if (uniqueActors.length > 0) {
      await Promise.all(uniqueActors.map(async (actorId) => {
        try {
          const response = await API.get(`${API.USER}${actorId}/`)
          // API.get wraps single objects in an array: [object]
          const userData = Array.isArray(response) ? response[0] : response
          
          if (userData) {
            const fullName = (userData.name ? `${userData.name} ${userData.last_name || ''}` : '').trim()
            actorDetails.value[actorId] = fullName || userData.username || 'Usuario desconocido'
          }
        } catch (e) {
          console.warn(`Could not fetch details for actor ${actorId}`, e)
          actorDetails.value[actorId] = 'Sistema'
        }
      }))
    }
  } catch (error) {
    console.error('Error fetching activity logs:', error)
  }
}

// Track if component is mounted to prevent updates during transitions
const isMounted = ref(false)
const pageReady = ref(false)
// User information
const userName = computed(() => authStore.fullName || 'User')
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
    title: 'Dispositivos Activos',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'info',
    key: 'infrastructure'
  },
  {
    title: 'Gateways',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'success',
    key: 'infrastructure'
  },
  {
    title: 'Clientes',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'warning',
    key: 'tenants'
  },
  {
    title: 'Usuarios Totales',
    value: '...',
    change: '',
    trend: 'neutral',
    icon: null,
    color: 'error',
    key: 'management'
  }
])

const visibleMetrics = computed(() => {
  return metrics.value.filter(m => {
    if (m.key === 'infrastructure') return canAccessInfrastructure.value
    if (m.key === 'tenants') return canAccessTenants.value
    if (m.key === 'management') return canAccessManagement.value
    return true
  })
})

// Recent activity from notifications
/* Lines 427-466 removed to use combined activity logic */

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

// Fetch real metrics from API
async function fetchMetrics() {
  try {
    // Fetch only what user has access to
    const fetchPromises = [
      canAccessInfrastructure.value ? API.get(API.DEVICE) : Promise.resolve(null),
      canAccessInfrastructure.value ? API.get(API.GATEWAY) : Promise.resolve(null),
      canAccessTenants.value ? API.get(API.TENANT) : Promise.resolve(null),
      canAccessUsers.value ? API.get(API.USER) : Promise.resolve(null),
      canAccessManagement.value ? fetchActivity() : Promise.resolve(null)
    ]
    
    const [devicesResponse, gatewaysResponse, tenantsResponse, usersResponse] = await Promise.all(fetchPromises)
    
    // Calculate device counts
    let activeDevices = '0'
    let deviceTotal = '0'
    if (devicesResponse) {
      const deviceCount = Array.isArray(devicesResponse) ? devicesResponse.length : devicesResponse?.count || 0
      const activeCount = Array.isArray(devicesResponse) 
        ? devicesResponse.filter(d => d.is_active || d.status === 'active').length 
        : deviceCount
      activeDevices = activeCount.toString()
      deviceTotal = `${deviceCount} total`
    }
    
    // Calculate gateway count
    let gatewayCountStr = '0'
    if (gatewaysResponse) {
      const gatewayCount = Array.isArray(gatewaysResponse) ? gatewaysResponse.length : gatewaysResponse?.count || 0
      gatewayCountStr = gatewayCount.toString()
    }
    
    // Calculate tenant count
    let tenantCountStr = '0'
    if (tenantsResponse) {
      const tenantCount = Array.isArray(tenantsResponse) ? tenantsResponse.length : tenantsResponse?.count || 0
      tenantCountStr = tenantCount.toString()
    }
    
    // Calculate user count
    let userCountStr = '0'
    if (usersResponse) {
      const userCount = Array.isArray(usersResponse) ? usersResponse.length : usersResponse?.count || 0
      userCountStr = userCount.toString()
    }
    
    // Update metrics values dynamically
    metrics.value.forEach(m => {
      if (m.title === 'Dispositivos Activos') {
        m.value = activeDevices
        m.change = deviceTotal
        m.trend = parseInt(activeDevices) > 0 ? 'up' : 'neutral'
        m.icon = icons.antenna
      }
      if (m.title === 'Gateways') {
        m.value = gatewayCountStr
        m.change = 'Conectados'
        m.trend = parseInt(gatewayCountStr) > 0 ? 'up' : 'neutral'
        m.icon = icons.wifi
      }
      if (m.title === 'Clientes') {
        m.value = tenantCountStr
        m.change = 'Organizaciones'
        m.trend = parseInt(tenantCountStr) > 0 ? 'up' : 'neutral'
        m.icon = icons.business
      }
      if (m.title === 'Usuarios Totales') {
        m.value = userCountStr
        m.change = 'Registrados'
        m.trend = parseInt(userCountStr) > 0 ? 'up' : 'neutral'
        m.icon = icons.people
      }
    })
  } catch (error) {
    console.error('Error fetching metrics:', error)
  }
}

// Permission-based visibility
const canAccessInfrastructure = computed(() => {
  const roles = ['technician', 'tenant_admin', 'tenant_user']
  return authStore.isSuperUser || authStore.isGlobalUser || roles.includes(authStore.user?.role_type) || authStore.isTenantAdmin
})

const canAccessGateways = computed(() => canAccessInfrastructure.value)
const canAccessApplications = computed(() => canAccessInfrastructure.value)
const canAccessMachines = computed(() => canAccessInfrastructure.value)

const canAccessManagement = computed(() => {
  const roles = ['manager', 'tenant_admin', 'tenant_user', 'viewer']
  return authStore.isSuperUser || authStore.isGlobalUser || roles.includes(authStore.user?.role_type) || authStore.isTenantAdmin
})

const canAccessUsers = computed(() => {
  const roles = ['manager', 'tenant_admin', 'tenant_user']
  return authStore.isSuperUser || authStore.isGlobalUser || roles.includes(authStore.user?.role_type) || authStore.isTenantAdmin
})

const canAccessWorkspaces = computed(() => canAccessManagement.value)

const canAccessTenants = computed(() => {
  return authStore.isSuperUser || authStore.isGlobalUser
})

const canAccessInbox = computed(() => {
  return authStore.isSuperUser || authStore.isSupportUser
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
  background: rgba(var(--ion-color-orange-500-rgb), 0.1);
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

/* Base Card Style matching other tables */
.table-card {
  margin: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  background: var(--ion-background-color, #fff);
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--ion-color-light);
  border-radius: 12px;
  margin: 16px;
}

.data-table {
  min-width: 1100px;
  margin: 0;
}

.table-header {
  background: var(--ion-color-light-shade, #f4f5f8);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  color: var(--ion-color-step-600);
}

.table-header ion-col {
  padding: 16px 12px;
}

.table-row-stylized {
  border-bottom: 1px solid var(--ion-color-light);
  transition: background-color 0.2s ease;
  align-items: center;
}

.table-row-stylized:hover {
  background-color: var(--ion-color-light-tint);
}

.table-row-stylized ion-col {
  padding: 14px 12px;
  display: flex;
  align-items: center;
}

.action-chip {
  font-size: 10px;
  height: 24px;
  margin: 0;
  font-weight: 700;
  text-transform: uppercase;
  --background: opacity(0.1);
}

.entity-chip {
  height: 22px;
  margin: 0;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: capitalize;
}

.actor-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.actor-icon {
  font-size: 14px;
  color: var(--ion-color-medium);
}

.change-log {
  font-size: 0.82rem;
  color: var(--ion-color-dark);
  font-weight: 400;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.activity-icon-small {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  flex-shrink: 0;
}

.activity-icon-small ion-icon {
  font-size: 16px;
}

.user-username {
  font-weight: 500;
  color: var(--ion-color-dark);
}

.user-email {
  color: var(--ion-color-medium);
  font-size: 0.85rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--ion-color-medium);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
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

  .role-chip,
  .platform-chip {
    border-color: var(--ion-color-dark);
  }
}
</style>
