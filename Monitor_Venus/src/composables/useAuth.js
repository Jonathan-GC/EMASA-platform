// Composable for accessing auth store easily in components
// Use this in your components instead of importing the store directly
import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore.js'

/**
 * Composable que expone funcionalidad de autenticación
 * Usar en componentes: const { user, isSuperUser, needsTenantSetup } = useAuth()
 */
export function useAuth() {
  const authStore = useAuthStore()

  return {
    // State
    user: computed(() => authStore.user),
    isAuthenticated: computed(() => authStore.isAuthenticated),
    isLoading: computed(() => authStore.isLoading),

    // Role checks
    isSuperUser: computed(() => authStore.isSuperUser),
    isGlobalUser: computed(() => authStore.isGlobalUser),
    isAdmin: computed(() => authStore.isAdmin),
    isNormalUser: computed(() => authStore.isNormalUser),

    // Tenant checks
    hasTenant: computed(() => authStore.hasTenant),
    needsTenantSetup: computed(() => authStore.needsTenantSetup),
    tenantId: computed(() => authStore.tenantId),

    // User info
    username: computed(() => authStore.username),
    userId: computed(() => authStore.userId),

    // Actions
    login: authStore.login,
    logout: authStore.logout,
    refreshToken: authStore.refreshToken,
    hasRole: authStore.hasRole,
    canAccessRoute: authStore.canAccessRoute,
  }
}
