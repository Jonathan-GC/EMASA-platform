// Token Management Utility
class TokenManager {
  constructor() {
    this.ACCESS_TOKEN_KEY = 'access_token';
    this.ACCESS_TOKEN_EXPIRY_KEY = 'access_token_expiry';
    this.ACCESS_TOKEN_DURATION = 60 * 60 * 1000; // 60 minutos
    this.REFRESH_BUFFER = 5 * 60 * 1000; // 5 minutos buffer para refresh
  }

  // Guardar access token en sessionStorage
  saveAccessToken(token) {
    if (!token) return false;
    
    try {
      sessionStorage.setItem(this.ACCESS_TOKEN_KEY, token);
      const expirationTime = Date.now() + this.ACCESS_TOKEN_DURATION;
      sessionStorage.setItem(this.ACCESS_TOKEN_EXPIRY_KEY, expirationTime.toString());
      
      console.log('💾 Access token guardado, expira en 60 minutos');
      return true;
    } catch (error) {
      console.error('❌ Error guardando access token:', error);
      return false;
    }
  }

  // Obtener access token válido
  getAccessToken() {
    try {
      const token = sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
      const expiry = sessionStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      
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
      const expiry = sessionStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
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
      const expiry = sessionStorage.getItem(this.ACCESS_TOKEN_EXPIRY_KEY);
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
      sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
      sessionStorage.removeItem(this.ACCESS_TOKEN_EXPIRY_KEY);
      console.log('🗑️ Access token eliminado');
    } catch (error) {
      console.error('❌ Error limpiando access token:', error);
    }
  }

  // Verificar si hay token válido
  hasValidToken() {
    return this.getAccessToken() !== null;
  }

  // Obtener información del token
  getTokenInfo() {
    const token = this.getAccessToken();
    const timeRemaining = this.getTimeRemaining();
    const shouldRefresh = this.shouldRefreshToken();
    
    return {
      hasToken: !!token,
      token: token ? token.substring(0, 20) + '...' : null,
      timeRemaining,
      shouldRefresh,
      isExpired: timeRemaining === 0 && sessionStorage.getItem(this.ACCESS_TOKEN_KEY)
    };
  }
}

// Exportar instancia singleton
export default new TokenManager();
