<template>
  <ion-page>
    <div class="app-container">
      <!-- Sidebar (NavBar vertical) en la izquierda -->
      <div class="sidebar">
        <NavBar />
      </div>
      
      <!-- Contenido principal en la derecha -->
      <div class="main-content">
        <ion-router-outlet :animation="customPushAnimation" />
      </div>
    </div>
  </ion-page>
</template>

<script setup>
import { provide } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import { createAnimation } from '@ionic/vue'

/**
 * Initialize global notification system
 * - WebSocket connection persists across all routes
 * - Available to all child components via inject('notifications')
 */
const notificationSystem = useNotifications()
provide('notifications', notificationSystem)

/**
 * Custom smooth push animation for page transitions
 */
const customPushAnimation = (baseEl, opts) => {
  const DURATION = 250

  const enteringAnimation = createAnimation()
    .addElement(opts.enteringEl)
    .duration(DURATION)
    .easing('ease-out')
    .fromTo('opacity', '0', '1')
    .fromTo('transform', 'translateX(30px)', 'translateX(0)')

  const leavingAnimation = createAnimation()
    .addElement(opts.leavingEl)
    .duration(DURATION)
    .easing('ease-out')
    .fromTo('opacity', '1', '0.3')

  const animation = createAnimation()
    .addAnimation([enteringAnimation, leavingAnimation])

  return animation
}
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100%;
}

.sidebar {
  width: 250px; /* Ancho fijo del sidebar */
  min-width: 250px;
  height: 100%; /* Altura completa de la pantalla */
  background-color: var(--ion-color-light, #f4f5f8); /* Sin fondo azul */
  border-right: 1px solid var(--ion-color-light, #f4f5f8);
  overflow-y: auto;
}

/* Hacer que el NavBar ocupe toda la altura disponible */
.sidebar :deep(nav),
.sidebar :deep(.navbar),
.sidebar :deep(.nav-container) {
  min-height: 100%;
}

.main-content {
  flex: 1; /* Toma el resto del espacio */
  height: 100%;
  position: relative;
  overflow: hidden;
  background: var(--ion-background-color, #f4f5f8);
}

/* Ensure ion-router-outlet fills the container properly */
.main-content :deep(ion-router-outlet) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* Ensure child pages have solid backgrounds */
.main-content :deep(ion-page) {
  background: var(--ion-background-color, #f4f5f8);
}

/* Responsive: En móviles, el sidebar se convierte en overlay */
@media (max-width: 768px) {
  .sidebar {
    width: 0; /* No ocupa espacio porque es overlay */
    min-width: 0;
    overflow: visible; /* Permite que el overlay se vea */
    border-right: none;
  }
  
  .main-content {
    width: 100%;
  }
}

/* Responsive: En pantallas muy pequeñas, el sidebar sigue sin ocupar espacio */
@media (max-width: 480px) {
  .sidebar {
    width: 0;
    min-width: 0;
  }
}
</style>
