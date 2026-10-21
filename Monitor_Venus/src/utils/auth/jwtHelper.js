// JWT Helper Utility
// Decodifica tokens JWT y extrae información del usuario
import { jwtDecode } from 'jwt-decode';

/**
 * Decodifica un JWT token y retorna el payload
 * @param {string} token - JWT token a decodificar
 * @returns {object|null} - Payload decodificado o null si hay error
 */
export const decodeToken = (token) => {
  if (!token) {
    console.warn('⚠️ No se proporcionó token para decodificar');
    return null;
  }

  try {
    const decoded = jwtDecode(token);
    console.log('✅ Token decodificado exitosamente:', {
      user_id: decoded.user_id,
      username: decoded.username,
      is_superuser: decoded.is_superuser,
      is_support: decoded.is_support,
      is_global: decoded.is_global
    });
    return decoded;
  } catch (error) {
    console.error('❌ Error decodificando token:', error.message);
    return null;
  }
};

/**
 * Extrae información del usuario desde el token JWT
 * @param {string} token - JWT token
 * @returns {object} - Información estructurada del usuario
 */
export const getUserFromToken = (token) => {
  const decoded = decodeToken(token);
  
  if (!decoded) {
    return {
      user_id: null,
      username: null,
      is_superuser: false,
      is_global: false,
      is_support: false,
      is_tenant_admin: false,
      has_hall_pass: false,
      role_type: null,
      tenant_id: null,
      cs_tenant_id: null,
      exp: null,
      iat: null
    };
  }

  return {
    user_id: decoded.user_id || null,
    username: decoded.username || null,
    is_superuser: decoded.is_superuser || false,
    is_global: decoded.is_global || false,
    is_support: decoded.is_support || false,
    is_tenant_admin: decoded.is_tenant_admin || false,
    has_hall_pass: decoded.has_hall_pass || false,
    role_type: decoded.role_type || null,
    tenant_id: decoded.tenant_id || null,
    cs_tenant_id: decoded.cs_tenant_id || null,
    exp: decoded.exp || null,
    iat: decoded.iat || null
  };
};

/**
 * Verifica si el token ha expirado basándose en el campo 'exp'
 * @param {string} token - JWT token
 * @returns {boolean} - true si el token está expirado
 */
export const isTokenExpired = (token) => {
  const decoded = decodeToken(token);
  
  if (!decoded || !decoded.exp) {
    return true;
  }

  // exp está en segundos, Date.now() en milisegundos
  const currentTime = Math.floor(Date.now() / 1000);
  const isExpired = decoded.exp < currentTime;
  
  if (isExpired) {
    console.warn('⏰ Token expirado');
  }
  
  return isExpired;
};

/**
 * Obtiene el tiempo restante hasta que expire el token (en segundos)
 * @param {string} token - JWT token
 * @returns {number} - Segundos restantes, 0 si ya expiró
 */
export const getTokenTimeRemaining = (token) => {
  const decoded = decodeToken(token);
  
  if (!decoded || !decoded.exp) {
    return 0;
  }

  const currentTime = Math.floor(Date.now() / 1000);
  const timeRemaining = decoded.exp - currentTime;
  
  return Math.max(0, timeRemaining);
};

/**
 * Helpers para verificar roles del usuario
 */
export const userRoleHelpers = {
  /**
   * Verifica si el usuario es superusuario
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  isSuperUser: (token) => {
    const user = getUserFromToken(token);
    return user.is_superuser === true;
  },

  /**
   * Verifica si el usuario es global (puede ver múltiples tenants)
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  isGlobalUser: (token) => {
    const user = getUserFromToken(token);
    return user.is_global === true;
  },

  /**
   * Verifica si el usuario pertenece a un tenant específico
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  hasTenant: (token) => {
    const user = getUserFromToken(token);
    return (user.tenant_id || user.cs_tenant_id) !== null;
  },

  /**
   * Verifica si el usuario es administrador (superuser O global)
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  isAdmin: (token) => {
    const user = getUserFromToken(token);
    return user.is_superuser === true || user.is_global === true;
  },

    /**
   * Verifica si el usuario es un usuario de soporte (no admin, no global)
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  isSupportUser: (token) => {
    const user = getUserFromToken(token);
    return is_support;
  },

  /**
   * Verifica si el usuario es un usuario normal (no admin, no global)
   * @param {string} token - JWT token
   * @returns {boolean}
   */
  isNormalUser: (token) => {
    const user = getUserFromToken(token);
    return !user.is_superuser && !user.is_global;
  },
  
};

/**
 * Formatea información del token para debugging
 * @param {string} token - JWT token
 * @returns {string} - String formateado con info del token
 */
export const formatTokenInfo = (token) => {
  const user = getUserFromToken(token);
  const timeRemaining = getTokenTimeRemaining(token);
  const minutes = Math.floor(timeRemaining / 60);
  
  return `
🔐 Token Info:
  - Usuario: ${user.username || 'N/A'}
  - ID: ${user.user_id || 'N/A'}
  - SuperUser: ${user.is_superuser ? '✅' : '❌'}
  - Global: ${user.is_global ? '✅' : '❌'}
  - Soporte: ${user.is_support ? '✅' : '❌'}
  - Tenant ID: ${user.tenant_id || user.cs_tenant_id || 'N/A'}
  - Expira en: ${minutes} minutos
  `;
};

export default {
  decodeToken,
  getUserFromToken,
  isTokenExpired,
  getTokenTimeRemaining,
  userRoleHelpers,
  formatTokenInfo
};
