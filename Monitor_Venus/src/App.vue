<template>
  <ion-app>
    <ion-router-outlet />
  </ion-app>
</template>

<script setup>
import { onMounted } from 'vue'
import { IonApp, IonRouterOutlet } from '@ionic/vue'
import { useAuthStore } from '@/stores/authStore.js'

// Initialize auth store when app loads
const authStore = useAuthStore()

onMounted(() => {
  console.log('🚀 App montada - Inicializando autenticación...')
  authStore.initializeAuth()
})
</script>
