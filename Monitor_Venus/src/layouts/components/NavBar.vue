<template>
  <!-- Backdrop para cerrar cuando se hace clic fuera (solo móvil) -->
  <div 
    v-if="isOpen" 
    class="backdrop"
    @click="closeNavbar"
  ></div>
  
  <nav class="navbar" :class="{ 'mobile-overlay': isOpen }">
    <!-- Botón hamburger solo visible en móvil -->
    <button 
      class="nav-toggle"
      @click="toggleNavbar"
      :class="{ active: isOpen }"
    >
      <span></span>
      <span></span>
      <span></span>
    </button>
    
    <div class="nav-container">
      <!-- Header del navbar con logo -->
      <div class="nav-header">
        <div class="nav-brand">
          <img src="../../assets/monitor_logo.svg" alt="Logo" class="nav-logo" />
        </div>
      </div>
      
      <!-- Links del navegador -->
      <div class="nav-links">
        <!-- Enlaces públicos (siempre visibles) -->
        <router-link 
          to="/home" 
          class="nav-link"
          :class="{ active: $route.path === '/home' }"
          @click="closeNavbar"
        >
          <ion-icon
              :icon="icons.home"
          ></ion-icon>
          Inicio
        </router-link>
        <router-link 
          to="/about" 
          class="nav-link"
          :class="{ active: $route.path === '/about' }"
          @click="closeNavbar"
        >
          <ion-icon
              :icon="icons.info"
          ></ion-icon>
           Acerca de
        </router-link>

        <!-- Enlaces para usuarios autenticados -->
        <template v-if="authStore.isAuthenticated">
          <router-link 
            :to="paths.NOTIFICATIONS"
            class="nav-link"
            :class="{ active: $route.path === paths.NOTIFICATIONS }"
            @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.notifications"
            ></ion-icon>
            Notificationes
          </router-link>
        </template>
        
        <!-- Enlaces de administración -->
        <template v-if="canAccessAnyAdminRoute && !authStore.isSupportUser && !authStore.isTechnician">
          <hr class="divider"/>
          
          <!-- Tenants: root, admin, manager -->
          <router-link
              v-if="canAccessRoute(['root', 'admin'])"
              to="/tenants"
              class="nav-link"
              :class="{ active: $route.path === '/tenants' }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.building"
            ></ion-icon>
            Clientes
          </router-link>

          <!-- Workspaces: root, admin, manager, viewer, tenant_admin, tenant_user -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'manager', 'viewer', 'tenant_admin', 'tenant_user'])"
              :to=paths.TENANT_WORKSPACES
              class="nav-link"
              :class="{ active: $route.path === paths.TENANT_WORKSPACES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.layers"
            ></ion-icon>
            Workspaces
          </router-link>

          <!-- Users: root, admin, manager, tenant_admin, tenant_user -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'manager', 'tenant_admin', 'tenant_user'])"
              :to="paths.USERS"
              class="nav-link"
              :class="{ active: $route.path === paths.USERS }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.person"
            ></ion-icon>
            Usuarios
          </router-link>

          <!-- Roles: root, admin, manager, tenant_admin, tenant_user -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'manager', 'tenant_admin', 'tenant_user'])"
              :to="paths.ROLES"
              class="nav-link"
              :class="{ active: $route.path === paths.ROLES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.shield"
            ></ion-icon>
            Roles
          </router-link>

          <!-- Locations: root, admin -->
          <router-link
              v-if="canAccessRoute(['root', 'admin'])"
              :to="paths.TENANT_LOCATIONS"
              class="nav-link"
              :class="{ active: $route.path === paths.TENANT_LOCATIONS }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.location"
            ></ion-icon>
            Ubicaciones
          </router-link>
        </template>

        <!-- Enlaces de infraestructura -->
        <template v-if="canAccessAnyInfrastructureRoute && !authStore.isSupportUser">

          <hr class="divider"/>
          
          <!-- Gateways: root, admin, technician, tenant_admin, tenant_user -->
          <router-link 
            v-if="canAccessRoute(['root', 'admin', 'technician', 'tenant_admin', 'tenant_user'])"
            to="/infrastructure/gateways"
            class="nav-link"
            :class="{ active: $route.path === paths.GATEWAYS }"
            @click="closeNavbar"
          >
          <ion-icon
                :icon="icons.wifi"
            ></ion-icon>  
            Gateways
          </router-link>
          
          <!-- Device Profiles: root, admin, technician -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'technician'])"
              :to=paths.DEVICE_PROFILES
              class="nav-link"
              :class="{ active: $route.path === paths.DEVICE_PROFILES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.options"
            ></ion-icon>
            Perfiles de nodos
          </router-link>

          <!-- Applications: root, admin, technician, tenant_admin, tenant_user -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'technician', 'tenant_admin', 'tenant_user'])"
              :to=paths.APPLICATIONS
              class="nav-link"
              :class="{ active: $route.path === paths.APPLICATIONS }"
              @click="closeNavbar"
          >
            <ion-icon :icon="icons.package" />
            Servicios
          </router-link>

          <!-- Machines: root, admin, technician, tenant_admin, tenant_user -->
          <router-link
              v-if="canAccessRoute(['root', 'admin', 'technician', 'tenant_admin', 'tenant_user'])"
              :to=paths.MACHINES
              class="nav-link"
              :class="{ active: $route.path === paths.MACHINES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.settings"
            ></ion-icon>
            Máquinas
          </router-link>
        </template>

        <!-- Support navbar !-->
        
          <hr class="divider"/>
          <router-link
            v-if="!showSupportLinks"
            :to="paths.SUPPORT"
            class="nav-link"
            :class="{ active: $route.path === paths.SUPPORT }"
            @click="closeNavbar"
          >
            <ion-icon :icon="icons.helpBuoy"></ion-icon>
            Soporte
          </router-link>
          <template v-if="authStore.isAuthenticated">
          <router-link
            v-if="showSupportLinks"
            :to="paths.INBOX"
            class="nav-link"
            :class="{ active: $route.path === paths.INBOX }"
            @click="closeNavbar"
          >
            <ion-icon :icon="icons.mail"></ion-icon>
            Inbox
          </router-link>
        </template>

        <!-- Inbox navbar !-->

        <template>

        

        </template>

        <hr class="divider"/>

        <!-- Enlaces de autenticación -->
        <router-link 
          v-if="showAuthLinks"
          to="/" 
          class="nav-link"
          :class="{ active: $route.path === '/auth' }"
          @click="closeNavbar"
        >
          🔑 Iniciar Sesión
        </router-link>
        
        <BtnLogout v-if="authStore.isAuthenticated"/>
      </div>
    </div>
  </nav>
</template>

<script setup>
import {inject, ref, computed} from 'vue'
import { useRoute } from 'vue-router'
import { paths } from "@/plugins/router/paths"
import BtnLogout from "@layouts/components/BtnLogout.vue";
import { useAuthStore } from '@/stores/authStore'

const icons = inject('icons', {})
const authStore = useAuthStore()

const $route = useRoute()
const isOpen = ref(false)

const toggleNavbar = () => {
  isOpen.value = !isOpen.value
}

const closeNavbar = () => {
  isOpen.value = false
}

// Helper function to check if user can access route with any of the required roles
const canAccessRoute = (requiredRoles) => {
  if (!authStore.isAuthenticated) return false
  return requiredRoles.some(role => authStore.hasRole(role))
}

// Check if user can access any admin route (to show the admin section)
const canAccessAnyAdminRoute = computed(() => {
  return canAccessRoute(['root', 'admin', 'manager', 'viewe r', 'tenant_admin', 'tenant_user'])
})

// Check if user can access any infrastructure route (to show the infrastructure section)
const canAccessAnyInfrastructureRoute = computed(() => {
  return canAccessRoute(['root', 'admin', 'technician', 'tenant_admin', 'tenant_user'])
})

const showAuthLinks = computed(() => {
  return !authStore.isAuthenticated
})

const showSupportLinks = computed(() => {
  return authStore.isSupportUser 
})

</script>

