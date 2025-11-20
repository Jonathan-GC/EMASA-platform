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
    is_support: false,
    is_tenant_admin: false,
    role_type: null, // 'technician', 'viewer', 'tenant_user', etc.
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
   * Verifica si el usuario es un usuario normal
   */
  const isNormalUser = computed(() => 
    !user.value.is_superuser && !user.value.is_global
  );

  /**
   * Verifica si el usuario es un usuario de soporte
   */
  const isSupportUser = computed(() => user.value.is_support === true);
  
  /**
   * Verifica si el usuario pertenece a un administrador de tenant 
   */
  const isTenantAdmin = computed(() => user.value.is_tenant_admin === true);

  /**
   * Verifica si el usuario es un técnico
   */
  const isTechnician = computed(() => user.value.role_type === 'technician');

  /**
   * Verifica si el usuario es un viewer (solo lectura)
   */
  const isViewer = computed(() => user.value.role_type === 'viewer');

  /**
   * Verifica si el usuario es un usuario de tenant (tenant_user)
   * Un tenant_user es un usuario regular que:
   * - NO es superuser
   * - NO es global
   * - NO es support
   * - NO es tenant_admin
   * - TIENE un tenant asignado (cs_tenant_id)
   */
  const isTenantUser = computed(() => 
    !user.value.is_superuser &&
    !user.value.is_global &&
    !user.value.is_support &&
    !user.value.is_tenant_admin &&
    user.value.cs_tenant_id !== null
  );

  /**
   * Verifica si el usuario es un manager (tenant manager)
   */
  const isManager = computed(() => 
    user.value.is_tenant_admin === true || user.value.role_type === 'manager'
  );

  /**
   * Verifica si el usuario pertenece a un tenant
   */
  const hasTenant = computed(() => user.value.cs_tenant_id !== null);  /**
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
      is_global: userData.is_global,
      is_support: userData.is_support,
      is_tenant_admin: userData.is_tenant_admin,
      tenant_id: userData.cs_tenant_id
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
      is_support: userData.is_support,
      tenant_id: userData.cs_tenant_id,
      is_tenant_admin: userData.is_tenant_admin
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
      is_support: false,
      is_tenant_admin: false,
      role_type: null,
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
   * Refresca el access token usando el refresh token de la cookie httpOnly
   * El backend lee el refresh_token de la cookie automáticamente
   * @returns {Promise<string>} - Nuevo access token
   */
  const refreshAccessToken = async () => {
    console.log('🔄 Intentando refresh token desde cookie httpOnly...');
    
    try {
      // NO enviamos refresh_token en el body, el backend lo lee de la cookie
      const response = await fetch('/api/v1/token/refresh/', {
        method: 'POST',
        credentials: 'include', // ← Crucial: Envía la cookie httpOnly
        headers: { 
          'Content-Type': 'application/json',
          // Agregar CSRF token si existe
          'X-CSRFToken': document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1] || ''
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ Refresh falló:', response.status, errorData);
        throw new Error('REFRESH_FAILED');
      }
      
      const data = await response.json();
      
      if (!data.access) {
        throw new Error('NO_ACCESS_TOKEN_IN_RESPONSE');
      }
      
      // Guardar nuevo access token
      tokenManager.saveAccessToken(data.access);
      
      // Actualizar store con nuevo token decodificado
      const userData = getUserFromToken(data.access);
      user.value = userData;
      
      console.log('✅ Token refrescado exitosamente desde cookie httpOnly');
      return data.access;
      
    } catch (error) {
      console.error('❌ Error refrescando token:', error.message);
      // Limpiar todo y forzar re-login
      logout();
      throw error;
    }
  };

  /**
   * Verifica si el usuario tiene un rol específico
   * @param {string} role - Role name to check
   * @returns {boolean}
   */
  const hasRole = (role) => {
    switch (role.toLowerCase()) {
      case 'root':
      case 'superuser':
        return isSuperUser.value;
      case 'admin':
        return isGlobalUser.value;
      case 'global':
        return isGlobalUser.value;
      case 'manager':
      case 'tenant_admin':
        return isManager.value;
      case 'technician':
        return isTechnician.value;
      case 'viewer':
        return isViewer.value;
      case 'tenant_user':
        return isTenantUser.value;
      case 'support':
        return isSupportUser.value;
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
    isTenantAdmin,
    isManager,
    isTechnician,
    isViewer,
    isTenantUser,
    isNormalUser,
    isSupportUser,
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
    refreshAccessToken,
    hasRole,
    canAccessRoute
  };
});
