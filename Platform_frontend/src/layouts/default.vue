<template>
  <ion-page>
    <div class="app-container">
      <!-- Sidebar (NavBar vertical) en la izquierda -->
      <div class="sidebar">
        <NavBar />
      </div>
      
      <!-- Contenido principal en la derecha -->
      <div class="main-content">
        <ion-content>
          <ion-router-outlet />
        </ion-content>
      </div>
    </div>
  </ion-page>
</template>

<script setup>
// NavBar se auto-importa
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
  height: 100vh; /* Altura completa de la pantalla */
  background-color: transparent; /* Sin fondo azul */
  border-right: 1px solid var(--ion-color-light, #f4f5f8);
  overflow-y: auto;
}

/* Hacer que el NavBar ocupe toda la altura disponible */
.sidebar :deep(nav),
.sidebar :deep(.navbar),
.sidebar :deep(.nav-container) {
  height: 100%;
  min-height: 100vh;
}

.main-content {
  flex: 1; /* Toma el resto del espacio */
  height: 100%;
}

.main-content ion-content {
  --background: var(--ion-color-light, #f4f5f8);
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
