<template>
  <div class="user-avatar-container" @click="handleClick">
    <div class="user-avatar" :class="avatarSize">
      <img 
        v-if="userProfileImage" 
        :src="userProfileImage" 
        :alt="displayName"
        class="avatar-image"
      />
      <div v-else class="avatar-initials" :style="{ backgroundColor: avatarColor }">
        {{ initials }}
      </div>
      
      <!-- Tenant Badge -->
      <div v-if="showTenantBadge && hasTenant" class="tenant-badge" :class="badgeSize">
        <img 
          v-if="tenantImage" 
          :src="tenantImage" 
          :alt="tenantName"
          class="tenant-image"
        />
        <div v-else class="tenant-initials">
          {{ tenantInitials }}
        </div>
      </div>
    </div>
    <div v-if="showName" class="user-info">
      <span class="user-name">{{ displayName }}</span>
      <span v-if="showRole" class="user-role">{{ userRole }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'

const props = defineProps({
  size: {
    type: String,
    default: 'medium', // 'small', 'medium', 'large'
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  showName: {
    type: Boolean,
    default: true
  },
  showRole: {
    type: Boolean,
    default: true
  },
  clickable: {
    type: Boolean,
    default: true
  },
  profileImage: {
    type: String,
    default: null
  },
  showTenantBadge: {
    type: Boolean,
    default: true
  },
  tenantImage: {
    type: String,
    default: null
  },
  tenantName: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['click'])

const authStore = useAuthStore()
const router = useRouter()

// Compute avatar size class
const avatarSize = computed(() => `avatar-${props.size}`)

// Compute badge size class
const badgeSize = computed(() => `badge-${props.size}`)

// Get user's display name - prioritize profile data
const displayName = computed(() => {
  if (props.showName && authStore.fullName) {
    return authStore.fullName
  }
  return authStore.userProfile?.username || authStore.user?.username || 'Usuario'
})

// Get profile image from store or props
const userProfileImage = computed(() => {
  return props.profileImage || authStore.profileImage
})

// Check if user has tenant
const hasTenant = computed(() => {
  return authStore.hasTenant || props.tenantName || authStore.profileTenantId
})

// Get tenant ID for potential tenant image fetching
const userTenantId = computed(() => {
  return authStore.profileTenantId || authStore.tenantId
})

const tenantImage = computed(() => {
  return props.tenantImage || authStore.profileTenantImage
})

// Get tenant initials
const tenantInitials = computed(() => {
  const name = props.tenantName || 'T'
  if (!name) return 'T'
  
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return name.substring(0, 1).toUpperCase()
})

// Get user's initials
const initials = computed(() => {
  const name = displayName.value
  if (!name) return 'U'
  
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
})

// Get user's role
const userRole = computed(() => {
  if (authStore.isSuperUser) return 'Super Admin'
  if (authStore.isGlobalUser) return 'Admin Global'
  if (authStore.isSupportUser) return 'Soporte'
  if (authStore.isTenantAdmin) return 'Admin'
  if (authStore.isManager) return 'Manager'
  if (authStore.isTechnician) return 'Técnico'
  if (authStore.isViewer) return 'Viewer'
  return 'Usuario'
})

// Generate a consistent color based on username
const avatarColor = computed(() => {
  const colors = [
    '#3b82f6', // blue
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#f59e0b', // amber
    '#10b981', // green
    '#06b6d4', // cyan
    '#6366f1', // indigo
    '#f97316', // orange
  ]
  
  const username = displayName.value
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const index = Math.abs(hash) % colors.length
  return colors[index]
})

// Handle click event
const handleClick = () => {
  if (props.clickable) {
    emit('click')
    // You can navigate to a profile page here
    // router.push('/profile')
  }
}

// Debug watcher to check profile image
watch(() => authStore.profileImage, (newVal) => {
  console.log('👤 Profile image updated:', newVal)
}, { immediate: true })

watch(() => userProfileImage.value, (newVal) => {
  console.log('🖼️ UserAvatar computed profileImage:', newVal)
}, { immediate: true })
</script>

<style scoped>
.user-avatar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  transition: background-color 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.user-avatar-container:hover {
  background-color: rgba(0, 0, 0, 0.05);
  cursor: pointer;
}

.user-avatar {
  position: relative;
  border-radius: 50%;
  overflow: visible;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tenant-badge {
  position: absolute;
  bottom: -2px;
  left: -2px;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  border: 2px solid white;
  overflow: hidden;
}

.badge-small {
  width: 14px;
  height: 14px;
  border-width: 1.5px;
}

.badge-medium {
  width: 18px;
  height: 18px;
}

.badge-large {
  width: 24px;
  height: 24px;
  border-width: 3px;
}

.tenant-image {
  width: 19px;
  height: 19px;
  object-fit: cover;
}

.tenant-initials {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  font-weight: 700;
  font-size: 8px;
  user-select: none;
}

.badge-large .tenant-initials {
  font-size: 11px;
}

.avatar-small {
  width: 32px;
  height: 32px;
}

.avatar-medium {
  width: 40px;
  height: 40px;
}

.avatar-large {
  width: 56px;
  height: 56px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-initials {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
  user-select: none;
  border-radius: 50%;
}

.avatar-small .avatar-initials {
  font-size: 12px;
}

.avatar-large .avatar-initials {
  font-size: 20px;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ion-text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: var(--ion-color-medium);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .user-avatar-container {
    padding: 6px;
  }
  
  .user-name {
    font-size: 13px;
  }
  
  .user-role {
    font-size: 11px;
  }
}
</style>
