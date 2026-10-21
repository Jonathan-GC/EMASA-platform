<template>
  <div v-if="workspaces.length > 0" class="workspace-switcher">
    <div class="filter-field">
      <span>
        
        - Workspace -
      </span>
      <!-- Mismo selector/modal que usa ModalSelector en el resto de forms de la app -->
      <ModalSelector
        class="custom"
        :model-value="activeWorkspaceId"
        :options="workspaces"
        value-field="id"
        display-field="name"
        :search-fields="['name']"
        title="Cambiar workspace"
        placeholder="Selecciona"
        search-placeholder="Buscar workspace..."
        @update:model-value="onSelect"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import ModalSelector from '@components/ui/ModalSelector.vue'

const icons = inject('icons', {})
const authStore = useAuthStore()

const workspaces = computed(() => authStore.availableWorkspaces)
const activeWorkspaceId = computed(() => authStore.activeWorkspaceId)

// ModalSelector emite el valor del campo 'value-field' (el id del workspace)
const onSelect = (value) => {
  // Cambia el workspace e incrementa contextVersion -> las vistas se remontan
  // y vuelven a consultar con el nuevo header X-Workspace-ID (sin recargar la página).
  authStore.switchWorkspace(value)
}
</script>

<style scoped>
.workspace-switcher {
  border-bottom: 1px solid rgba(222, 226, 230, 0.6);
  width: 100%;
}

/* Mismo patrón visual que los filtros de las tablas (p.ej. Auditoría) */
.filter-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
}

.filter-field span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--ion-color-medium);
  padding-left: 4px;
}

/* El trigger por defecto de ModalSelector es un botón gris (bg-zinc-300).
   Se re-estiliza con :deep() para que sea una copia del .filter-select de las tablas */
.workspace-switcher :deep(.modal-selector-button) {
  display: flex;
  align-items: center;
  width: 100%;
  height: 56px;
  box-sizing: border-box;
  padding: 0 12px;
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-radius: 6px;
  background: var(--ion-card-background, #fff);
  font-size: 16px;
  color: var(--ion-text-color);
}

/* Chevron igual al del ion-select: pequeño, gris, pegado a la derecha */
.workspace-switcher :deep(.modal-selector-button .dropdown-icon) {
  font-size: 1.25rem;
  color: rgba(var(--ion-text-color-rgb, 0, 0, 0), 0.54);
  flex-shrink: 0;
}

/* Texto con ellipsis si el nombre es largo, como el ion-select */
.workspace-switcher :deep(.modal-selector-button span) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Placeholder con la misma opacidad que --placeholder-opacity del ion-select */
.workspace-switcher :deep(.modal-selector-button .text-gray-500) {
  opacity: 0.9;
}
</style>
