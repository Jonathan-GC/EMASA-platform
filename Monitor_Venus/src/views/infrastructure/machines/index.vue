<template>
  <ion-page>

    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="current-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon :icon="icons.settings"></ion-icon>
              Panel de Maquinas
            </h1>
          </div>
        </div>
        <!-- Main gateways table with fetch data -->
        <TableMachines />
      </div>

      <!-- Loading state while page is preparing -->
      <div v-else class="page-loading">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Preparando página...</p>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import TableGateways from '@components/tables/gateways/TableGateways.vue'

// State for connection status
const isConnected = ref(true)
const reconnectAttempts = ref(0)
const pageReady = ref(false)
const icons = inject('icons', {})

// Ionic lifecycle hooks
onIonViewWillEnter(() => {
  console.log('🚀 Gateway page will enter')
  pageReady.value = false
})

onIonViewDidEnter(() => {
  console.log('✅ Gateway page did enter')
  pageReady.value = true
})

onMounted(() => {
  console.log('🔧 Gateway page mounted')
})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.current-dashboard {
  padding: 20px;
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
