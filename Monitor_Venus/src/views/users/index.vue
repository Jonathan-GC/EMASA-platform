<script setup>
import { inject, ref } from "vue";
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue';
import TableUsers from "@components/tables/users/TableUsers.vue";

const icons = inject('icons', {})

// Ionic cachea las páginas: onMounted no se vuelve a disparar al re-entrar.
// pageReady fuerza el remount de la tabla para no mostrar datos obsoletos.
const pageReady = ref(false)

onIonViewWillEnter(() => {
  pageReady.value = false
})

onIonViewDidEnter(() => {
  pageReady.value = true
})
</script>

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="current-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon :icon="icons.people"></ion-icon>
              Usuarios
            </h1>
          </div>
        </div>
        <!-- Users information section -->
        <TableUsers />
      </div>

      <!-- Loading state while page is preparing -->
      <div v-else class="page-loading">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Preparando página...</p>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
@import '@assets/css/dashboard.css';

.header {
  margin-bottom: 30px;
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
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
