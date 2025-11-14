<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>Roles</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="roles-view">
        <!-- Header -->
        <div class="header">
          <h1>🎭 Gestión de Roles</h1>
          <div class="header-subtitle">
            <p>Administra roles y permisos del sistema</p>
          </div>
        </div>
        
        <!-- Main roles table -->
        <TableRoles />
      </div>
      
      <!-- Loading state -->
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
import TableRoles from '@components/tables/roles/TableRoles.vue'

const pageReady = ref(false)

// Ionic lifecycle hooks
onIonViewWillEnter(() => {
  console.log('🚀 Roles page will enter')
  pageReady.value = false
})

onIonViewDidEnter(() => {
  console.log('✅ Roles page did enter')
  pageReady.value = true
})

onMounted(() => {
  console.log('🔧 Roles page mounted')
})
</script>

<style scoped>
.roles-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2rem;
  margin-bottom: 10px;
  color: var(--ion-color-primary);
}

.header-subtitle p {
  color: var(--ion-color-medium);
  font-size: 1rem;
}

.page-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
}

.page-loading ion-spinner {
  margin-bottom: 16px;
}

.page-loading p {
  color: var(--ion-color-medium);
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .roles-view {
    padding: 10px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
