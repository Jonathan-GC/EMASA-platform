<script setup lang="ts">
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import API from '@/utils/api/api.js'

// Router instance
const router = useRouter()

// Auth store
const authStore = useAuthStore()

// Icons from plugin
const icons = inject('icons', {})

// Loading state
const loading = ref(false)

// Logout handler
const handleLogout = async () => {
  loading.value = true

  try {
    console.log('🚪 Iniciando proceso de logout...')

    // 1. Make logout request to backend first (optional, can be fire and forget)
    API.post(API.LOGOUT).catch(error => {
      console.warn('⚠️ Error en logout request:', error.message)
    })

    // 2. Clear auth store (this clears sessionStorage and cookies)
    authStore.logout()

    // 3. Clear all tokens from API instance
    API.clearAllTokens()

    console.log('🧹 Sesión cerrada, redirigiendo...')

    // 4. Force full page reload to reset everything
    // This ensures:
    // - All Vue components are destroyed and recreated
    // - All stores are reset to initial state
    // - Router is completely reinitialized
    // - No stale data remains in memory
    router.push('/home')

  } catch (error) {
    console.error('❌ Error durante logout:', error)
    // Even if there's an error, clear everything and reload
    authStore.logout()
    API.clearAllTokens()
    router.push('/home')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <ion-button
    @click="handleLogout"
    :disabled="loading"
    color="danger"
    fill="clear"
    size="small"
  >
    <ion-icon :icon="icons.logOut" slot="start"></ion-icon>
    <span v-if="!loading">Cerrar Sesión</span>
    <ion-spinner v-else name="crescent" style="width: 16px; height: 16px;"></ion-spinner>
  </ion-button>
</template>

<style scoped>
ion-button {
  --color: var(--ion-color-danger);
}

ion-button:hover {
  --color: var(--ion-color-danger-shade);
}

ion-spinner {
  margin-right: 8px;
}
</style>