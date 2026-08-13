<template>
  <div class="floating-action-buttons">
    <QuickControl 
      v-if="showRefresh || (showCreate && canCreate)"
      :toRefresh="showRefresh" 
      :toCreate="showCreate && canCreate" 
      :type="entityType" 
      @refresh="$emit('refresh')" 
      @itemCreated="$emit('itemCreated')" 
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import QuickControl from './quickControl.vue'
import { useAuthStore } from '@/stores/authStore'

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
</style>
