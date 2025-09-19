<template>
  <div class="login-container">
    <ion-card class="form-card">
      <ion-card-header class="text-center">
        <ion-card-title>¡Bienvenido!</ion-card-title>
        <ion-card-subtitle>Ingresa con tu cuenta de monitor</ion-card-subtitle>
      </ion-card-header>
      
      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Autenticando...</p>
        </div>

        <!-- Login form -->
        <div v-else>
          <ion-item>
            <ion-label position="stacked" class="!mb-2">Email</ion-label>
            <ion-input 
              v-model="credentials.username"
              type="text"
              placeholder="example@mail.com"
              :disabled="loading"
              class="bg-zinc-300 rounded-md p-100 form-field"
              fill="solid"
            ></ion-input>
          </ion-item>

          <ion-item>
            <ion-label position="stacked" class="!mb-2">Contraseña</ion-label>
            <ion-input 
              v-model="credentials.password"
              type="password"
              placeholder="*****"
              :disabled="loading"
              @keyup.enter="handleLogin"
              class="bg-zinc-300 rounded-md p-100"
              fill="solid"
            ></ion-input>
          </ion-item>

          <!-- Error message -->
          <ion-item v-if="error" lines="none" class="error-item">
            <ion-label color="danger">
              <ion-icon :icon="icons.alertCircle"></ion-icon>
              {{ error }}
            </ion-label>
          </ion-item>

          <!-- Success message -->
          <ion-item v-if="success" lines="none" class="success-item">
            <ion-label color="success">
              <ion-icon :icon="icons.success"></ion-icon>
              {{ success }}
            </ion-label>
          </ion-item>

          <!-- Info note -->

          <!-- CSRF Status -->

          <!-- Access Token Status -->

          <!-- Buttons -->
          <div class="button-container">


            <ion-button 
              expand="block"
              color="dark"
              @click="handleLogin"
              :disabled="loading || !credentials.username || !credentials.password"
            >
              <ion-icon :icon="icons.key" slot="start"></ion-icon>
              Iniciar Sesión
            </ion-button>

            <ion-button 
              expand="block" 
              fill="clear" 
              color="medium" 
              @click="checkCookies"
            >
              <ion-icon :icon="icons.eye" slot="start"></ion-icon>
              Ver Cookies
            </ion-button>

            <ion-button 
              expand="block" 
              fill="clear" 
              color="danger" 
              @click="logout"
            >
              <ion-icon :icon="icons.logOut" slot="start"></ion-icon>
              Cerrar Sesión
            </ion-button>
            <p class="text-center">¿No tienes cuenta? <router-link :to="paths.REGISTER">Regístrate</router-link></p>
          </div>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, inject, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import API from '@utils/api/index.js'
import {paths}  from '@/plugins/router/paths.js'

// Router instance
const router = useRouter()

// Iconos desde el plugin
const icons = inject('icons', {})

// Estado reactivo
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const cookieInfo = ref(null)

// Credenciales del usuario
const credentials = ref({
  username: '',
  password: ''
})

// Estado del CSRF token (reactivo)
const csrfStatus = computed(() => {
  const token = getCookieValue('csrftoken');
  if (token) {
    return {
      message: '✅ Token CSRF disponible',
      class: 'csrf-available',
      token: token
    };
  } else {
    return {
      message: '❌ Token CSRF no encontrado',
      class: 'csrf-missing',
      token: null
    };
  }
})

// Estado del Access Token (reactivo)
const tokenStatus = computed(() => {
  const token = sessionStorage.getItem('access_token');
  const expiry = sessionStorage.getItem('access_token_expiry');
  
  if (token && expiry) {
    const now = Date.now();
    const expiryTime = parseInt(expiry);
    const timeLeft = expiryTime - now;
    
    if (timeLeft > 0) {
      const minutesLeft = Math.floor(timeLeft / (1000 * 60));
      return {
        message: `✅ Access token válido (${minutesLeft} min restantes)`,
        class: 'token-valid',
        token: token.substring(0, 20) + '...',
        minutesLeft
      };

    } else {
      return {
        message: '⚠️ Access token expirado',
        class: 'token-expired',
        token: null,
        minutesLeft: 0
      };
    }
  } else {
    return {
      message: '❌ No hay access token',
      class: 'token-missing',
      token: null,
      minutesLeft: 0
    };
  }
})

// Función para limpiar mensajes
const clearMessages = () => {
  error.value = null
  success.value = null
}

// Función helper para obtener el valor de una cookie
const getCookieValue = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Función helper para obtener headers con CSRF token
const getHeadersWithCSRF = (additionalHeaders = {}) => {
  const csrfToken = getCookieValue('csrftoken');
  const headers = { ...additionalHeaders };
  
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
    console.log('🛡️ CSRF Token agregado al header:', csrfToken);
  } else {
    console.warn('⚠️ No se encontró CSRF token en las cookies');
  }
  
  return headers;
}

// Función principal de auth
const handleLogin = async () => {
  if (!credentials.value.username || !credentials.value.password) {
    error.value = 'Por favor ingresa usuario y contraseña'
    return
  }

  loading.value = true
  clearMessages()

  try {
    console.log('🔑 Intentando auth con:', {
      username: credentials.value.username,
      password: '***'
    })

    // Verificar si existe CSRF token, si no, obtenerlo primero
    let csrfToken = getCookieValue('csrftoken');
    if (!csrfToken) {
      console.log('🛡️ No hay CSRF token, obteniendo uno...');
      await getCsrfToken();
      // Pequeña pausa para que se establezca la cookie
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // Obtener headers con CSRF token
    const headers = getHeadersWithCSRF();

    // Realizar auth con CSRF token
    const response = await API.post(API.TOKEN, {
      username: credentials.value.username,
      password: credentials.value.password
    }, headers)

    console.log('✅ Login exitoso:', response)
    
    // Guardar tokens en sessionStorage
    if (response && response.length > 0) {
      const loginData = response[0]; // API.handleResponse retorna array
      
      if (loginData.access) {
        sessionStorage.setItem('access_token', loginData.access);
        console.log('💾 Access token guardado en sessionStorage');
        
        // Calcular tiempo de expiración (60 minutos)
        const expirationTime = Date.now() + (60 * 60 * 1000);
        sessionStorage.setItem('access_token_expiry', expirationTime.toString());
        console.log('⏰ Token expira en 60 minutos');
      }
      
      if (loginData.refresh) {
        // El refresh se maneja por cookies, pero podemos loggearlo
        console.log('🔄 Refresh token recibido (manejado por cookies)');
      }
    }
    
    success.value = '¡Login exitoso! Tokens guardados.'
    
    // Redirigir a /tenants después de un segundo
    setTimeout(() => {
      router.push('/tenants');
    }, 500);

    // Verificar cookies después del auth
    setTimeout(checkCookies, 1000)

  } catch (err) {
    console.error('❌ Error en auth:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

// Función para refresh token
const refreshToken = async () => {
  loading.value = true
  clearMessages()

  try {
    console.log('🔄 Intentando refresh token...')
    
    // Obtener headers con CSRF token
    const headers = getHeadersWithCSRF();
    
    const response = await API.post(API.REFRESH_TOKEN, {}, headers)
    
    console.log('✅ Token refreshed:', response)
    success.value = 'Token refreshed exitosamente!'
    
    setTimeout(checkCookies, 1000)

  } catch (err) {
    console.error('❌ Error en refresh:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

// Función para obtener CSRF token
const getCsrfToken = async () => {
  loading.value = true
  clearMessages()

  try {
    console.log('🛡️ Obteniendo CSRF token...')
    
    const response = await API.get(API.CSRF_TOKEN)
    
    console.log('✅ CSRF token obtenido:', response)
    success.value = 'CSRF token obtenido exitosamente!'
    
    setTimeout(checkCookies, 1000)

  } catch (err) {
    console.error('❌ Error obteniendo CSRF:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

// Función para verificar cookies
const checkCookies = () => {
  console.log('🍪 Verificando cookies...')
  
  const cookies = document.cookie.split(';').reduce((acc, cookie) => {
    const [name, value] = cookie.trim().split('=')
    acc[name] = value
    return acc
  }, {})

  console.log('🍪 Cookies encontradas:', cookies)
  
  const relevantCookies = {
    csrftoken: cookies.csrftoken || 'No encontrada',
    refresh_token: cookies.refresh_token || 'No encontrada',
    sessionid: cookies.sessionid || 'No encontrada',
    access_token: cookies.access_token || 'No encontrada'
  }

  cookieInfo.value = JSON.stringify(relevantCookies, null, 2)
}

// Función para logout
const logout = async () => {
  loading.value = true
  clearMessages()

  try {
    console.log('🚪 Cerrando sesión...')
    
    // Limpiar tokens de sessionStorage
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('access_token_expiry');
    console.log('🗑️ Tokens eliminados de sessionStorage');
    
    // Limpiar cookies manualmente
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'
    
    // Limpiar credenciales
    credentials.value = { username: '', password: '' }
    cookieInfo.value = null
    
    success.value = 'Sesión cerrada exitosamente!'
    
    console.log('✅ Logout exitoso')

  } catch (err) {
    console.error('❌ Error en logout:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

// Verificar cookies al montar el componente
checkCookies()
</script>

<style scoped>
.form-card{
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.login-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}

.loading-container {
  text-align: center;
  padding: 20px;
}

.loading-container ion-spinner {
  margin-bottom: 16px;
}

.error-item {
  margin: 10px 0;
}

.success-item {
  margin: 10px 0;
}

.button-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.button-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-card {
  margin: 15px 0;
  background-color: var(--ion-color-light);
}

.info-card ion-card-content {
  padding: 12px;
}

.info-card p {
  margin: 5px 0;
  font-size: 14px;
  line-height: 1.4;
}

.info-card code {
  background-color: var(--ion-color-medium);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.csrf-status, .token-status {
  margin: 10px 0;
  background-color: var(--ion-color-light-tint);
  border-radius: 8px;
}

.csrf-available, .token-valid {
  color: var(--ion-color-success);
  font-weight: 500;
}

.csrf-missing, .token-missing {
  color: var(--ion-color-danger);
  font-weight: 500;
}

.token-expired {
  color: var(--ion-color-warning);
  font-weight: 500;
}

.csrf-token, .access-token {
  margin-top: 5px;
  word-break: break-all;
}

.csrf-token code, .access-token code {
  background-color: var(--ion-color-dark);
  color: var(--ion-color-light);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
}

.cookie-info {
  margin-top: 20px;
  padding: 16px;
  background-color: var(--ion-color-light);
  border-radius: 8px;
  border: 1px solid var(--ion-color-medium);
}

.cookie-info h4 {
  margin: 0 0 10px 0;
  color: var(--ion-color-primary);
}

.cookie-info pre {
  background-color: var(--ion-color-dark);
  color: var(--ion-color-light);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  margin: 0;
}

ion-item {
  margin-bottom: 10px;
}

ion-input {
  margin-top: 5px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .login-container {
    padding: 10px;
  }
  
  .cookie-info pre {
    font-size: 10px;
  }
}
</style>
