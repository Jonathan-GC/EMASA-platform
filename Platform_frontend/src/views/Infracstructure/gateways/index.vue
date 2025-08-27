<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>Gateways</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="gateways-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <h1>🌐 Panel de Gateways</h1>
          <div class="header-subtitle">
            <ConnectionStatus 
              :is-connected="isConnected" 
              :reconnect-attempts="reconnectAttempts" 
            />
          </div>
        </div>
        <!-- Main gateways table with fetch data -->
        <GatewaysTable />
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
import { ref, onMounted } from 'vue'
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import GatewaysTable from '@components/tables/gateways/GatewaysTable.vue'

// State for connection status
const isConnected = ref(true)
const reconnectAttempts = ref(0)
const pageReady = ref(false)

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
.gateways-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 24px;
  text-align: center;
}

.header h1 {
  margin: 0 0 8px 0;
  #color: var(--ion-color-primary);
  font-size: 2rem;
}

.header-subtitle {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.comparison-section {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 2px solid var(--ion-color-light);
}

.comparison-section h2 {
  text-align: center;
  color: var(--ion-color-primary);
  margin-bottom: 8px;
}

.comparison-note {
  text-align: center;
  color: var(--ion-color-medium);
  font-style: italic;
  margin-bottom: 24px;
}

.tables-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.table-section h3 {
  color: var(--ion-color-secondary);
  margin-bottom: 16px;
  text-align: center;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .gateways-dashboard {
    padding: 16px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
  
  .tables-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .header-subtitle {
    flex-direction: column;
    gap: 8px;
  }
}

.page-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 16px;
}

.page-loading p {
  color: var(--ion-color-medium);
  margin: 0;
}
</style>
