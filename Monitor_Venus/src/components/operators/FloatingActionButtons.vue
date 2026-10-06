<template>
  <div v-if="visible" class="floating-action-buttons">
    <ion-button
      v-if="showClear"
      fill="clear"
      shape="round"
      class="mx-2 floating-utility"
      title="Limpiar filtros"
      aria-label="Limpiar filtros"
      @click="$emit('clear')"
    >
      <ion-icon :icon="closeOutline" slot="icon-only"></ion-icon>
    </ion-button>

    <ion-button
      v-if="showFilter"
      fill="clear"
      shape="round"
      class="mx-2 floating-utility"
      title="Filtros"
      aria-label="Filtros"
      @click="$emit('filter')"
    >
      <ion-icon :icon="optionsOutline" slot="icon-only"></ion-icon>
    </ion-button>

    <QuickControl 
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
import { optionsOutline, closeOutline } from 'ionicons/icons'
import QuickControl from './quickControl.vue'
import { useAuthStore } from '@/stores/authStore'
import { useResponsiveView } from '@/composables/useResponsiveView.js'

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
  },
  /**
   * Whether to show the clear-filters button
   */
  showClear: {
    type: Boolean,
    default: false
  },
  /**
   * Whether to show the filter button
   */
  showFilter: {
    type: Boolean,
    default: false
  },
  /**
   * Whether the floating buttons are restricted to mobile viewports.
   * Set to false for pages that intentionally show them on desktop too.
   */
  mobileOnly: {
    type: Boolean,
    default: true
  }
})

// Emits
defineEmits(['refresh', 'itemCreated', 'clear', 'filter'])

const { isMobile } = useResponsiveView(768)

const visible = computed(() => !props.mobileOnly || isMobile.value)

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

/* Give the refresh chip the same visual weight as the create button, which
   renders as fill="solid" and picks up a Material elevation shadow.
   Scoped to this component on purpose: the same refresh button in the desktop
   toolbar sits on a white card, where a white fill would lose its edge.
   The clear and filter buttons reuse the exact same treatment via
   .floating-utility so all three utility buttons look identical. */
.floating-action-buttons :deep(.quick-control-refresh),
.floating-action-buttons .floating-utility {
  --background: #ffffff;
  --color: var(--ion-color-amber-500, #f97316);
  --background-hover: #f4f4f5;
  --background-focused: #f4f4f5;
  --background-activated: #e4e4e7;
  --background-hover-opacity: 0.08;
  --background-focused-opacity: 0.12;
  --background-activated-opacity: 0;
  --border-radius: 999px;
  --box-shadow: 0 3px 1px -2px rgba(0, 0, 0, 0.2),
                0 2px 2px 0 rgba(0, 0, 0, 0.14),
                0 1px 5px 0 rgba(0, 0, 0, 0.12);
}
</style>
