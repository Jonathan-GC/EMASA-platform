<script setup>
import {inject} from "vue";

const icons = inject('icons', {})

</script>

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="current-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon
                :icon="icons.building"
            ></ion-icon>
              Clientes
            </h1>
          </div>
        </div>
        <!-- Tenants information section -->
        <TableTenants />
      </  div>
    </ion-content>
  </ion-page>

</template>

<style scoped>
@import '@assets/css/dashboard.css';

.current-dashboard {
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0;
  width: fit-content;
}

.header-title ion-back-button {
  display: flex;
  align-items: center;
  margin: 0 !important;
  padding: 0 !important;
  --padding-start: 0;
  --padding-end: 0;
  --margin-start: 0;
  --margin-end: 0;
  --min-width: auto;
  height: auto;
}

.header-title h1 {
  margin: 0;
  padding: 0;
  color: #374151;
  font-size: 2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  line-height: 1;
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