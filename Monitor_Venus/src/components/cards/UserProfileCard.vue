<template>
  <div class="profile-card">
    <QuickActions v-if="isOwnProfile" class="profile-edit-action" type="user" :index="user.id"
      :name="user.username" to-edit :initial-data="sidebarInitialData" @item-edited="emit('edited')" />
    <UserAvatar size="large" :name="fullName" :profile-image="avatarSrc" :show-name="false" :show-role="false"
      :clickable="false" :show-tenant-badge="false" />
    <h2 class="profile-name">{{ fullName }}</h2>
    <p v-if="user.tenant_name" class="profile-tenant">{{ user.tenant_name }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
  isOwnProfile: { type: Boolean, default: false },
})

const emit = defineEmits(['edited'])

const fullName = computed(() => {
  const u = props.user
  if (!u) return ''
  const { name, last_name, username } = u
  if (name && last_name) return `${name} ${last_name}`
  if (name) return name
  return username || ''
})

const avatarSrc = computed(() => {
  const img = props.user?.img
  if (!img) return null
  if (img.startsWith('http://') || img.startsWith('https://')) return img
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  const imagePath = img.startsWith('/') ? img : `/${img}`
  return `${backendUrl}${imagePath}`
})

const sidebarInitialData = computed(() => {
  const u = props.user
  if (!u) return {}
  return {
    code: u.code,
    username: u.username,
    email: u.email,
    name: u.name,
    last_name: u.last_name,
    phone: u.phone,
    phone_code: u.phone_code,
    country: u.country,
    tenant: u.tenant?.id || u.tenant,
    is_active: u.is_active,
    img: u.img,
    address: u.address,
  }
})
</script>

<style scoped>
.profile-card {
  position: relative;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 32px 24px 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.profile-edit-action {
  position: absolute;
  top: 8px;
  right: 8px;
}

.profile-card :deep(.user-avatar-container) {
  justify-content: center;
  padding: 0;
  width: auto;
}

.profile-name {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--ion-text-color);
  text-align: center;
}

.profile-tenant {
  margin: 0;
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  text-align: center;
}

@media (max-width: 768px) {
  .profile-card {
    padding: 20px;
  }
}
</style>
