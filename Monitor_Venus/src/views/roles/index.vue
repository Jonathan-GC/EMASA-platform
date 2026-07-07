<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="current-dashboard">
        <!-- Header -->
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon :icon="icons.shield"></ion-icon>
              Roles
            </h1>
          </div>
        </div>
        
        <!--<div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon
                :icon="icons.building"
            ></ion-icon>
              Clientes
            </h1>
          </div>
        </div>-->
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
import { inject } from 'vue';
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue'


const pageReady = ref(false)
const icons = inject('icons', {})

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
@import '@assets/css/dashboard.css';
.roles-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
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
