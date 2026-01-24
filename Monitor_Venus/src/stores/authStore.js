// Auth Store - Maneja autenticación y roles de usuario
// Este store es el CENTRO de toda la lógica de autenticación
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import tokenManager from '@/utils/auth/tokenManager.js';
import { getUserFromToken, userRoleHelpers, isTokenExpired } from '@/utils/auth/jwtHelper.js';
import API from '@/utils/api/api.js';

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

  // User profile data from API.ME
  const userProfile = ref({
    id: null,
    code: null,
    username: null,
    email: null,
    img: null, // profile image URL
    name: null,
    last_name: null,
    tenant: null, // tenant ID
    is_active: true,
    phone: null,
    phone_code: null,
    address: null,
    tenant: {
      id:null,
      name:null,
      img:null,
    },
  });

  const isAuthenticated = ref(false);
  const isLoading = ref(false);
  const isLoadingProfile = ref(false);

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

  /**
   * Obtiene la imagen de perfil del usuario con URL completa
   */
  const profileImage = computed(() => {
    const img = userProfile.value.img;
    if (!img) return null;
    
    // If it's already a full URL, return it
    if (img.startsWith('http://') || img.startsWith('https://')) {
      return img;
    }
    
    // If it's a relative path, prepend the backend URL
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
    // Remove '/api/' from the end to get the backend base URL
    const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '');
    
    // Ensure the image path starts with /
    const imagePath = img.startsWith('/') ? img : `/${img}`;
    
    return `${backendUrl}${imagePath}`;
  });

  /**
   * Obtiene el nombre completo del usuario
   */
  const fullName = computed(() => {
    if (userProfile.value.name && userProfile.value.last_name) {
      return `${userProfile.value.name} ${userProfile.value.last_name}`;
    }
    return userProfile.value.name || userProfile.value.username || username.value;
  });

  /**
   * Obtiene el email del usuario
   */
  const email = computed(() => userProfile.value.email);

  /**
   * Obtiene el ID del tenant del perfil
   */
  const profileTenantId = computed(() => userProfile.value.tenant.id);

  /**
   * Obtiene el nombre del tenant del perfil
   */
  const profileTenantName = computed(() => userProfile.value.tenant.name);

  /**
   * Obtiene la imagen del tenant del perfil
   */
  const profileTenantImage = computed(() => {
    const img = userProfile.value.tenant.img;
    if (!img) return null;
    
    // If it's already a full URL, return it
    if (img.startsWith('http://') || img.startsWith('https://')) {
      return img;
    }
    
    // If it's a relative path, prepend the backend URL
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
    // Remove '/api/' from the end to get the backend base URL
    const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '');
    
    // Ensure the image path starts with /
    const imagePath = img.startsWith('/') ? img : `/${img}`;
    
    return `${backendUrl}${imagePath}`;
  });

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

    // Fetch user profile after initializing from token
    fetchUserProfile().catch(err => {
      console.warn('⚠️ Could not fetch user profile on init:', err);
    });

    return true;
  };

  /**
   * Hace login del usuario
   * @param {string} accessToken - Token JWT del backend
   * @param {string} refreshToken - Token de refresco (opcional)
   * @returns {boolean} - true si login exitoso
   */
  const login = (accessToken, refreshToken = null) => {
    console.log('🔐 Procesando login...');
    
    if (!accessToken) {
      console.error('❌ No se proporcionó token');
      return false;
    }

    // Guardar access token
    const saved = tokenManager.saveAccessToken(accessToken);
    
    // Guardar refresh token si se proporciona (útil para móvil/Capacitor)
    if (refreshToken) {
      tokenManager.saveRefreshToken(refreshToken);
    }
    
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
    
    // Limpiar todos los tokens (access + refresh)
    tokenManager.clearAllTokens();
    
    // Limpiar cookies
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    
    // Resetear store
    clearAuth();
    
    console.log('✅ Sesión cerrada');
  };

  /**
   * Fetches user profile data from API.ME endpoint
   * Called after successful login or on app initialization
   */
  const fetchUserProfile = async () => {
    if (!isAuthenticated.value) {
      console.log('⚠️ Not authenticated, skipping profile fetch');
      return false;
    }

    isLoadingProfile.value = true;
    
    try {
      console.log('📡 Fetching user profile from API.ME...');
      const response = await API.get(API.ME);
      
      console.log('🔍 API.ME raw response:', response);
      
      // API.handleResponse wraps objects in arrays, so unwrap it
      const userData = Array.isArray(response) ? response[0] : response;
      
      console.log('📦 Unwrapped user data:', userData);
      
      userProfile.value = {
        id: userData.id || null,
        code: userData.code || null,
        username: userData.username || null,
        email: userData.email || null,
        img: userData.img || null,
        name: userData.name || null,
        last_name: userData.last_name || null,
        tenant: userData.tenant || null,
        is_active: userData.is_active ?? true,
        phone: userData.phone || null,
        phone_code: userData.phone_code || null,
        address: userData.address || null,
        tenant: {
          id: userData.tenant?.id || null,
          name: userData.tenant?.name || null,
          img: userData.tenant?.img || null,
        }
      };

      console.log('✅ User profile loaded:', {
        username: userProfile.value.username,
        email: userProfile.value.email,
        hasImage: !!userProfile.value.img,
        imageUrl: userProfile.value.img,
        tenant: userProfile.value.tenant,
        fullName: `${userProfile.value.name} ${userProfile.value.last_name}`,
        tenantImage: profileTenantImage.value.tenant.img
      });

      return true;
    } catch (error) {
      console.error('❌ Error fetching user profile:', error);
      return false;
    } finally {
      isLoadingProfile.value = false;
    }
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
    userProfile.value = {
      id: null,
      code: null,
      username: null,
      email: null,
      img: null,
      name: null,
      last_name: null,
      tenant: null,
      is_active: true,
      phone: null,
      phone_code: null,
      address: null,
      tenant:{
        id:null,  
        name:null,
        img:null,
      }

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
   * Refresca el access token usando el refresh token guardado
   * Intenta primero usando cookies (HttpOnly) y luego usando body (para móvil/Capacitor)
   * @returns {Promise<string>} - Nuevo access token
   */
  const refreshAccessToken = async () => {
    console.log('🔄 Intentando refresh token...');
    
    try {
      // Get API base URL
      const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';
      const refreshUrl = `${apiBaseUrl}v1/token/refresh/`;
      
      console.log('🔗 Refresh URL:', refreshUrl);
      
      // Obtener refresh token de localStorage por si las cookies no funcionan (móvil)
      const storedRefreshToken = tokenManager.getRefreshToken();
      
      // Configuración de la petición
      const requestBody = {};
      if (storedRefreshToken) {
        requestBody.refresh = storedRefreshToken;
        console.log('📦 Refresh token incluido en el body (fallback móvil)');
      }

      // Intentar el refresh
      const response = await fetch(refreshUrl, {
        method: 'POST',
        credentials: 'include', // Envía cookies si están disponibles
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1] || ''
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'No error body');
        console.error('❌ Refresh falló:', response.status, errorText);
        throw new Error(`REFRESH_FAILED: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.access) {
        throw new Error('NO_ACCESS_TOKEN_IN_RESPONSE');
      }
      
      // Guardar nuevo access token
      tokenManager.saveAccessToken(data.access);
      
      // Si el backend devolvió un nuevo refresh token, guardarlo también
      if (data.refresh) {
        tokenManager.saveRefreshToken(data.refresh);
      }
      
      // Actualizar store con nuevo token decodificado
      const userData = getUserFromToken(data.access);
      user.value = userData;
      
      console.log('✅ Token refrescado exitosamente');
      return data.access;
      
    } catch (error) {
      console.error('❌ Error refrescando token:', error.message);
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
    userProfile,
    isAuthenticated,
    isLoading,
    isLoadingProfile,
    
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
    profileImage,
    fullName,
    email,
    profileTenantId,
    profileTenantName,
    profileTenantImage,
    
    // Actions
    initializeAuth,
    login,
    logout,
    fetchUserProfile,
    refreshToken,
    refreshAccessToken,
    hasRole,
    canAccessRoute
  };
});
