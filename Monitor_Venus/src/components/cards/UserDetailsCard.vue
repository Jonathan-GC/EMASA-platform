<template>
  <div class="details-card">
    <div class="detail-row">
      <span class="detail-label">Usuario</span>
      <span class="detail-value">@{{ user.username }}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Email</span>
      <span class="detail-value">{{ user.email || '-' }}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Estado</span>
      <ion-chip :color="user.is_active ? 'success' : 'danger'" size="small" class="detail-chip">
        {{ user.is_active ? 'Activo' : 'Suspendido' }}
      </ion-chip>
    </div>
    <div class="detail-row">
      <span class="detail-label">Rol</span>
      <div v-if="roles.length" class="role-chips">
        <ion-chip v-for="role in roles" :key="role.id || role.name" size="small" class="role-chip"
          :style="roleChipStyle(role)">
          {{ role.name }}
        </ion-chip>
      </div>
      <span v-else class="detail-value">-</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Código Fiscal</span>
      <span class="detail-value code-value">{{ user.code || '-' }}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Contacto</span>
      <span class="detail-value">{{ formatContact }}</span>
    </div>
    <div v-if="user.country" class="detail-row">
      <span class="detail-label">País</span>
      <span class="detail-value">{{ user.country }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
  roles: { type: Array, default: () => [] },
})

const formatContact = computed(() => {
  if (!props.user) return '-'
  const pc = props.user.phone_code || ''
  const p = props.user.phone
  if (p) return `${pc} ${p}`
  return '-'
})

const roleTextColor = (hex) => {
  if (!hex) return undefined
  const c = hex.replace('#', '')
  if (c.length < 6) return undefined
  const r = parseInt(c.substring(0, 2), 16)
  const g = parseInt(c.substring(2, 4), 16)
  const b = parseInt(c.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6 ? '#1f2937' : '#ffffff'
}

const roleChipStyle = (role) => {
  if (!role?.color) return {}
  return {
    'border': role.color ? `1px solid ${role.color}` : undefined,
    '--background': role.color + '80',
    '--color': roleTextColor(role.color),
  }
}
</script>

<style scoped>
.details-card {
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-label {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex-shrink: 0;
  margin-right: 12px;
}

.detail-value {
  font-size: 0.9rem;
  color: var(--ion-text-color);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.code-value {
  font-family: monospace;
  font-size: 0.85rem;
}

.detail-chip {
  margin: 0;
  height: 22px;
  font-size: 0.75rem;
}

.role-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.role-chip {
  margin: 0;
  height: 22px;
  font-size: 0.75rem;
}

@media (max-width: 768px) {
  .details-card {
    padding: 12px 16px;
  }
}
</style>
