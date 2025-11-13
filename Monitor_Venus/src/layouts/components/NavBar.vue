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
            Notifications
          </router-link>
        </template>
        
        <!-- Enlaces de administración (solo superuser y admin) -->
        <template v-if="showRootLinks">
          <hr class="divider"/>
          
          <router-link
              to="/tenants"
              class="nav-link"
              :class="{ active: $route.path === '/tenants' }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.building"
            ></ion-icon>
            Tenants
          </router-link>

          <router-link
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

          <router-link
              :to="paths.TENANT_MANAGERS"
              class="nav-link"
              :class="{ active: $route.path === paths.TENANT_MANAGERS }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.people"
            ></ion-icon>
            Managers
          </router-link>

          <router-link
              :to=paths.TENANT_LOCATIONS
              class="nav-link"
              :class="{ active: $route.path === paths.TENANT_LOCATIONS }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.location"
            ></ion-icon>
            Locations
          </router-link>
        </template>

        <!-- Enlaces de tenant (usuarios con tenant asignado) -->
        <template v-if="!showSupportLinks && showTenantLinks || showRootLinks">
          <hr class="divider"/>

          <router-link 
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
          
          <router-link
              :to=paths.DEVICE_PROFILES
              class="nav-link"
              :class="{ active: $route.path === paths.DEVICE_PROFILES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.options"
            ></ion-icon>
            Device Profiles
          </router-link>

          <router-link
              :to=paths.APPLICATIONS
              class="nav-link"
              :class="{ active: $route.path === paths.APPLICATIONS }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.package"
            ></ion-icon>
            Applications
          </router-link>

          <router-link
              :to=paths.MACHINES
              class="nav-link"
              :class="{ active: $route.path === paths.MACHINES }"
              @click="closeNavbar"
          >
            <ion-icon
                :icon="icons.settings"
            ></ion-icon>
            Maquinas
          </router-link>
        </template>

        <!-- Support navbar !-->
        <hr class="divider"/>
        <router-link
          :to="paths.SUPPORT"
          class="nav-link"
          :class="{ active: $route.path === paths.SUPPORT }"
          @click="closeNavbar"
        >
          <ion-icon :icon="icons.helpBuoy"></ion-icon>
          Support
        </router-link>

        <!-- Inbox navbar !-->

        <template v-if="!showSupportLinks && showTenantLinks || showRootLinks">

        <router-link
          :to="paths.INBOX"
          class="nav-link"
          :class="{ active: $route.path === paths.INBOX }"
          @click="closeNavbar"
        >
          <ion-icon :icon="icons.mail"></ion-icon>
          Inbox
        </router-link>

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

// Computed properties para mostrar/ocultar enlaces según roles
const showRootLinks = computed(() => {
  return authStore.isSuperUser
})

const showAdminLinks = computed(() => {
  return authStore.isAdmin && authStore.hasTenant
})

const showTenantLinks = computed(() => {
  return authStore.isAuthenticated && authStore.hasTenant
})
const showSupportLinks = computed(() => {
  return authStore.isSupportUser && authStore.hasTenant
})
 
const showAuthLinks = computed(() => {
  return !authStore.isAuthenticated
})

</script>

<style scoped>
/* Estilos base para desktop */
.navbar {
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
  padding: 1rem 0;
  height: 100%;
  min-height: 100vh;
  position: relative;
}

.nav-container {
  height: 100%;
  min-height: 100%;
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.nav-header {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-logo {
  height: 32px;
  width: 200px;
}

/* Botón hamburger - oculto en desktop */
.nav-toggle {
  display: none;
  position: fixed;
  top: 1rem;
  right: 1rem;
  flex-direction: column;
  cursor: pointer;
  padding: 12px;
  background: #ffffff;
  border: none;
  border-radius: 8px;
  gap: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1002;
  transition: all 0.3s ease;
}

.nav-toggle span {
  width: 25px;
  height: 3px;
  background: #495057;
  transition: 0.3s;
  border-radius: 3px;
}

/* Animación del botón hamburger */
.nav-toggle.active span:nth-child(1) {
  transform: rotate(-45deg) translate(-5px, 6px);
}

.nav-toggle.active span:nth-child(2) {
  opacity: 0;
}

.nav-toggle.active span:nth-child(3) {
  transform: rotate(45deg) translate(-5px, -6px);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 200px;
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: #ffffff;
  color: #6c757d;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid #dee2e6;
  text-align: center;
}

.nav-link:hover {
  background: #e9ecef;
  color: #495057;
  border-color: #adb5bd;
}

.nav-link.active {
  background: var(--ion-color-secondary);
  color: white;
  border-color: #495057;
}

/* Backdrop - solo visible en móvil */
.backdrop {
  display: none;
}

.divider{
  margin: 1rem 0;
  border-top: 1px solid #e9ecef;
}

/* Estilos para móvil - OVERLAY VERTICAL */
@media (max-width: 768px) {
  /* Navbar como overlay fijo */
  .navbar {
    position: fixed;
    top: 0;
    left: -280px; /* Oculto por defecto */
    width: 280px;
    height: 100vh;
    background: #ffffff;
    border-right: 1px solid #e9ecef;
    box-shadow: 2px 0 15px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow-y: auto;
  }
  
  /* Navbar visible cuando está abierto */
  .navbar.mobile-overlay {
    left: 0;
  }
  
  /* Backdrop para cerrar al hacer clic fuera */
  .backdrop {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    opacity: 0;
    animation: fadeIn 0.3s ease forwards;
  }
  
  @keyframes fadeIn {
    to { opacity: 1; }
  }
  
  /* Mostrar botón hamburger en móvil */
  .nav-toggle {
    display: flex;
  }
  
  .nav-container {
    padding: 1rem;
    gap: 2rem;
    min-height: 100%;
    justify-content: flex-start;
  }
  
  .nav-header {
    width: 100%;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e9ecef;
    margin-bottom: 1rem;
  }
  
  .nav-logo {
    height: 28px;
    width: 180px;
  }
  
  .nav-links {
    width: 100%;
    max-width: none;
    gap: 12px;
  }
  
  .nav-link {
    padding: 16px 20px;
    font-size: 1rem;
    justify-content: flex-start;
    border-radius: 12px;
    margin: 0;
  }
}

/* Para pantallas muy pequeñas */
@media (max-width: 480px) {
  .navbar {
    width: 260px;
    left: -260px;
  }
  
  .nav-logo {
    height: 24px;
    width: 150px;
  }
  
  .nav-link {
    padding: 14px 16px;
    font-size: 0.9rem;
  }


}
</style>
