<script setup>
import {inject} from "vue";

const icons = inject('icons', {})

</script>

<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>Monitor CLient Workspaces</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content :fullscreen="true">
      <div class="current-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <h1>
            <ion-icon
                :icon="icons.building"
            ></ion-icon>
            Workspaces de Clientes
          </h1>
        </div>
        <!-- Tenants information section -->
        <TableUsers />
      </div>
    </ion-content>
  </ion-page>

</template>

<style scoped>
@import '@assets/css/dashboard.css';

.current-dashboard {
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  margin: 0 0 15px 0;
  color: #374151;
  font-size: 2rem;
  font-weight: 600;
}

.header-subtitle {
  display: flex;
  justify-content: center;
  align-items: center;
}

.no-data {
  margin: 40px 0;
  text-align: center;
}

.no-data ion-card {
  max-width: 500px;
  margin: 0 auto;
}

.no-data h2 {
  color: #6b7280;
  margin: 0 0 10px 0;
}

.no-data p {
  color: #9ca3af;
  margin: 8px 0;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .current-dashboard {
    padding: 15px;
  }

  .header h1 {
    font-size: 1.5rem;
  }
}
</style>