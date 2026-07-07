// Token Management Utility
class TokenManager {
  constructor() {
    this.ACCESS_TOKEN_KEY = 'access_token';
    this.ACCESS_TOKEN_EXPIRY_KEY = 'access_token_expiry';
    this.REFRESH_TOKEN_KEY = 'refresh_token';
    this.ACCESS_TOKEN_DURATION = 60 * 60 * 1000; // 60 minutos
    this.REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutos buffer para refresh
  }

  // Guardar access token en localStorage (compartido entre tabs)
  saveAccessToken(token) {
    if (!token) return false;
    
    try {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
      const expirationTime = Date.now() + this.ACCESS_TOKEN_DURATION;
      localStorage.setItem(this.ACCESS_TOKEN_EXPIRY_KEY, expirationTime.toString());
      
      console.log('💾 Access token guardado en localStorage, expira en 60 minutos');
      return true;
    } catch (error) {
      console.error('❌ Error guardando access token:', error);
      return false;
    }
  }

  // Guardar refresh token en localStorage
  saveRefreshToken(token) {
    if (!token) return false;
    
    try {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
      console.log('💾 Refresh token guardado en localStorage');
      return true;
    } catch (error) {
      console.error('❌ Error guardando refresh token:', error);
      return false;
    }
  }

  // Obtener access token válido
  getAccessToken() {
    try {
      const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
      const expiry = localStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      
      if (!token || !expiry) return null;
      
      const now = Date.now();
      const expiryTime = parseInt(expiry);
      
      if (now >= expiryTime) {
        console.log('⚠️ Access token expirado');
        this.clearAccessToken();
        return null;
      }
      
      return token;
    } catch (error) {
      console.error('❌ Error obteniendo access token:', error);
      return null;
    }
  }

  // Verificar si el token expira pronto
  shouldRefreshToken() {
    try {
      const expiry = localStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      if (!expiry) return false;
      
      const now = Date.now();
      const expiryTime = parseInt(expiry);
      const timeUntilExpiry = expiryTime - now;
      
      // Refrescar si quedan menos de 5 minutos
      return timeUntilExpiry <= this.REFRESH_BUFFER;
    } catch (error) {
      console.error('❌ Error verificando expiración:', error);
      return false;
    }
  }

  // Obtener tiempo restante en minutos
  getTimeRemaining() {
    try {
      const expiry = localStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      if (!expiry) return 0;
      
      const now = Date.now();
      const expiryTime = parseInt(expiry);
      const timeLeft = expiryTime - now;
      
      return Math.max(0, Math.floor(timeLeft / (1000 * 60)));
    } catch (error) {
      console.error('❌ Error calculando tiempo restante:', error);
      return 0;
    }
  }

  // Limpiar access token
  clearAccessToken() {
    try {
      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      console.log('🗑️ Access token eliminado de localStorage');
    } catch (error) {
      console.error('❌ Error limpiando access token:', error);
    }
  }

  // Limpiar refresh token
  clearRefreshToken() {
    try {
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
      console.log('🗑️ Refresh token eliminado de localStorage');
    } catch (error) {
      console.error('❌ Error limpiando refresh token:', error);
    }
  }

  // Limpiar todos los tokens
  clearAllTokens() {
    this.clearAccessToken();
    this.clearRefreshToken();
  }

  // Obtener refresh token
  getRefreshToken() {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  // Verificar si hay token válido
  hasValidToken() {
    return this.getAccessToken() !== null;
  }

  // Obtener información del token
  getTokenInfo() {
    const token = this.getAccessToken();
    const refreshToken = this.getRefreshToken();
    const timeRemaining = this.getTimeRemaining();
    const shouldRefresh = this.shouldRefreshToken();
    
    return {
      hasToken: !!token,
      hasRefreshToken: !!refreshToken,
      token: token ? token.substring(0, 20) + '...' : null,
      timeRemaining,
      shouldRefresh,
      isExpired: timeRemaining === 0 && localStorage.getItem(this.ACCESS_TOKEN_KEY)
    };
  }
}

// Exportar instancia singleton
export default new TokenManager();
