<script setup lang="ts">
import { ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import API from '@/utils/api/api.js'

// Router instance
const router = useRouter()

// Icons from plugin
const icons = inject('icons', {})

// Loading state
const loading = ref(false)

// Logout handler
const handleLogout = async () => {
  loading.value = true

  try {
    console.log('🚪 Iniciando proceso de logout...')

    // 1. Clear all tokens from API instance FIRST (immediate)
    API.clearAllTokens()

    // 2. Clear additional cookies manually (immediate)
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'

    console.log('🧹 Tokens y cookies eliminados')

    // 3. Redirect immediately (don't wait for backend)
    router.push('/home')
    console.log('🏠 Redirigido a /home')

    // 4. Make logout request to backend (non-blocking, fire and forget)
    API.post(API.LOGOUT).catch(error => {
      console.warn('⚠️ Error en logout request (ya redirigido):', error.message)
    })

  } catch (error) {
    console.error('❌ Error durante logout:', error)
    // Even if there's an error, clear tokens and redirect
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