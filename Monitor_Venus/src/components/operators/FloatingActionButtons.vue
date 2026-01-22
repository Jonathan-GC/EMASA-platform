<template>
  <div class="floating-action-buttons">
    <!-- Refresh Button -->
    <ion-button 
      v-if="showRefresh"
      @click="$emit('refresh')" 
      color="primary" 
      shape="round" 
      class="fab-refresh"
    >
      <ion-icon :icon="icons.refresh" slot="icon-only"></ion-icon>
    </ion-button>
    
    <!-- Create Button -->
    <QuickControl 
      v-if="showCreate && canCreate"
      :toCreate="true" 
      :type="entityType" 
      @itemCreated="$emit('itemCreated')" 
    />
  </div>
</template>

<script setup>
import { inject, computed } from 'vue'
import { IonButton, IonIcon } from '@ionic/vue'
import QuickControl from './quickControl.vue'
import { useAuthStore } from '@/stores/authStore'

// Access icons from the plugin
const icons = inject('icons', {})
const authStore = useAuthStore()

// Props
const props = defineProps({
  /**
   * The entity type for QuickControl (e.g., 'tenant', 'gateway', 'device')
   */
  entityType: {
    type: String,
    required: true
  },
  /**
   * Whether to show the refresh button
   */
  showRefresh: {
    type: Boolean,
    default: true
  },
  /**
   * Whether to show the create button
   */
  showCreate: {
    type: Boolean,
    default: true
  }
})

// Emits
defineEmits(['refresh', 'itemCreated'])

const canCreate = computed(() => {
  if (authStore.isSuperUser || authStore.isGlobalUser || authStore.isTenantAdmin) return true
  
  const isManagement = ['tenant', 'user', 'workspace', 'role', 'location'].includes(props.entityType)
  const isInfrastructure = ['gateway', 'application', 'machine', 'device_profile', 'device_type', 'device'].includes(props.entityType)
  
  if (isManagement) return authStore.user?.role_type === 'manager'
  if (isInfrastructure) return ['manager', 'technician'].includes(authStore.user?.role_type)
  
  return false
})
</script>

<style scoped>
/* Floating Action Buttons (Mobile Only) */
.floating-action-buttons {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.fab-refresh {
  --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 40.333px;
  height: 40.333px;
}
</style>
