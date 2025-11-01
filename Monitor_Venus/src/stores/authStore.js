// Auth Store - Maneja autenticación y roles de usuario
// Este store es el CENTRO de toda la lógica de autenticación
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import tokenManager from '@/utils/auth/tokenManager.js';
import { getUserFromToken, userRoleHelpers, isTokenExpired } from '@/utils/auth/jwtHelper.js';

export const useAuthStore = defineStore('auth', () => {
  // ========================================
  // STATE - Información del usuario actual
  // ========================================
  
  const user = ref({
    user_id: null,
    username: null,
    is_superuser: false,
    is_global: false,
    cs_tenant_id: null,
    exp: null,
    iat: null
  });

  const isAuthenticated = ref(false);
  const isLoading = ref(false);

  // ========================================
  // GETTERS - Computed properties para acceso fácil
  // ========================================

  /**
   * Verifica si el usuario es superusuario
   */
  const isSuperUser = computed(() => user.value.is_superuser === true);

  /**
   * Verifica si el usuario es global (puede ver múltiples tenants)
   */
  const isGlobalUser = computed(() => user.value.is_global === true);

  /**
   * Verifica si el usuario es administrador (superuser O global)
   */
  const isAdmin = computed(() => 
    user.value.is_superuser === true || user.value.is_global === true
  );

  /**
   * Verifica si el usuario es un usuario normal
   */
  const isNormalUser = computed(() => 
    !user.value.is_superuser && !user.value.is_global
  );

  /**
   * Verifica si el usuario pertenece a un tenant
   */
  const hasTenant = computed(() => user.value.cs_tenant_id !== null);

  /**
   * Verifica si el usuario necesita configurar un tenant
   * TRUE si: no es global, no tiene tenant, y está autenticado
   */
  const needsTenantSetup = computed(() => {
    return (
      isAuthenticated.value &&
      !user.value.is_global &&
      user.value.cs_tenant_id === null &&
      !user.value.is_superuser // Superusers no necesitan tenant
    );
  });

  /**
   * Obtiene el ID del tenant del usuario
   */
  const tenantId = computed(() => user.value.cs_tenant_id);

  /**
   * Obtiene el nombre de usuario
   */
  const username = computed(() => user.value.username);

  /**
   * Obtiene el ID del usuario
   */
  const userId = computed(() => user.value.user_id);

  // ========================================
  // ACTIONS - Funciones para modificar el estado
  // ========================================

  /**
   * Inicializa el store desde el token guardado
   * Se llama al cargar la app para restaurar sesión
   */
  const initializeAuth = () => {
    console.log('🔄 Inicializando autenticación...');
    
    const token = tokenManager.getAccessToken();
    
    if (!token) {
      console.log('❌ No hay token guardado');
      clearAuth();
      return false;
    }

    if (isTokenExpired(token)) {
      console.log('⏰ Token expirado');
      clearAuth();
      return false;
    }

    // Decodificar token y poblar el store
    const userData = getUserFromToken(token);
    user.value = userData;
    isAuthenticated.value = true;

    console.log('✅ Autenticación inicializada:', {
      username: userData.username,
      is_superuser: userData.is_superuser,
      is_global: userData.is_global
    });

    return true;
  };

  /**
   * Hace login del usuario
   * @param {string} accessToken - Token JWT del backend
   * @returns {boolean} - true si login exitoso
   */
  const login = (accessToken) => {
    console.log('🔐 Procesando login...');
    
    if (!accessToken) {
      console.error('❌ No se proporcionó token');
      return false;
    }

    // Guardar token en sessionStorage
    const saved = tokenManager.saveAccessToken(accessToken);
    
    if (!saved) {
      console.error('❌ Error guardando token');
      return false;
    }

    // Decodificar y guardar info del usuario
    const userData = getUserFromToken(accessToken);
    user.value = userData;
    isAuthenticated.value = true;

    console.log('✅ Login exitoso:', {
      username: userData.username,
      is_superuser: userData.is_superuser,
      is_global: userData.is_global,
      tenant_id: userData.cs_tenant_id
    });

    return true;
  };

  /**
   * Hace logout del usuario
   * Limpia todo: store + sessionStorage + cookies
   */
  const logout = () => {
    console.log('👋 Cerrando sesión...');
    
    // Limpiar token
    tokenManager.clearAccessToken();
    
    // Limpiar cookies
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    
    // Resetear store
    clearAuth();
    
    console.log('✅ Sesión cerrada');
  };

  /**
   * Limpia la autenticación (helper interno)
   */
  const clearAuth = () => {
    user.value = {
      user_id: null,
      username: null,
      is_superuser: false,
      is_global: false,
      cs_tenant_id: null,
      exp: null,
      iat: null
    };
    isAuthenticated.value = false;
  };

  /**
   * Actualiza el token (para refresh)
   * @param {string} newAccessToken - Nuevo token JWT
   */
  const refreshToken = (newAccessToken) => {
    console.log('🔄 Refrescando token...');
    return login(newAccessToken);
  };

  /**
   * Verifica si el usuario tiene un rol específico
   * @param {string} role - 'superuser', 'admin', 'global', 'normal'
   * @returns {boolean}
   */
  const hasRole = (role) => {
    switch (role.toLowerCase()) {
      case 'superuser':
        return isSuperUser.value;
      case 'admin':
        return isAdmin.value;
      case 'global':
        return isGlobalUser.value;
      case 'normal':
        return isNormalUser.value;
      default:
        console.warn(`⚠️ Rol desconocido: ${role}`);
        return false;
    }
  };

  /**
   * Verifica si el usuario puede acceder a una ruta
   * Basado en los meta.roles de la ruta
   * @param {Array} requiredRoles - Roles requeridos ['superuser', 'admin', etc.]
   * @returns {boolean}
   */
  const canAccessRoute = (requiredRoles) => {
    if (!requiredRoles || requiredRoles.length === 0) {
      return true; // Ruta pública
    }

    // Si no está autenticado, no puede acceder
    if (!isAuthenticated.value) {
      return false;
    }

    // Verificar si tiene alguno de los roles requeridos
    return requiredRoles.some(role => hasRole(role));
  };

  // ========================================
  // RETURN - Exportar estado y funciones
  // ========================================

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    
    // Getters
    isSuperUser,
    isGlobalUser,
    isAdmin,
    isNormalUser,
    hasTenant,
    needsTenantSetup,
    tenantId,
    username,
    userId,
    
    // Actions
    initializeAuth,
    login,
    logout,
    refreshToken,
    hasRole,
    canAccessRoute
  };
});
