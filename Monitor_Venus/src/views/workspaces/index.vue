<script setup>
import { inject } from "vue";
import TableWorkspaces from "../../components/tables/workspaces/TableWorkspaces.vue";

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
              <ion-icon :icon="icons.layers"></ion-icon>
              Workspaces de Clientes
            </h1>
          </div>
        </div>
        <!-- Tenants information section -->
        <TableWorkspaces />
      </div>
    </ion-content>
  </ion-page>

</template>

<style scoped>
@import '@assets/css/dashboard.css';


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

  .header h1 {
    font-size: 1.5rem;
  }
}
</style>