<template>

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
          <!-- Wrap inputs in a native form so Enter submits the form -->
          <form @submit.prevent="handleLogin" @keydown.enter.prevent="onFormEnter">
          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Usuario</ion-label>
            <ion-input 
              v-model="credentials.username"
              type="text"
              placeholder="tu.usuario"
              :disabled="loading"
              class="bg-zinc-300 rounded-md p-100 form-field custom"
              fill="solid"
              :scroll-y="isMobile"
            ></ion-input>
          </ion-item>

          <div class="text-right">
          <PasswordInput
            v-model="credentials.password"
            label="Contraseña"
            placeholder="*****"
            :disabled="loading"
            class="mt-4"
          />
          <router-link :to="paths.RESET_PASSWORD_REQUEST" class="text-sm text-primary-600 text-right mt-2 no-underline">
              ¿Olvidaste tu contraseña?
          </router-link>
          </div>

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
              type="submit"
              expand="block"
              color="dark"
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

            <!-- Google Sign-In divider -->
            <div class="google-divider">
              <span>o</span>
            </div>

            <!-- Google Sign-In button -->
            <GoogleLoginButton />

            <!--<p class="text-center">¿No tienes cuenta? <router-link :to="paths.SIGNUP">Regístrate</router-link></p>-->
          </div>
          </form>
        </div>
      </ion-card-content>
    </ion-card>
 
</template>

<script setup>
import { ref, inject, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore.js'
import { useResponsiveView } from '@composables/useResponsiveView.js'
import API from '@utils/api/index.js'
import {paths}  from '@/plugins/router/paths.js'
import GoogleLoginButton from '@/components/common/GoogleLoginButton.vue'
import { registerPush } from '@composables/usePushNotifications.js'

// Router instance
const router = useRouter()

// Responsive view detection
const { isMobile } = useResponsiveView(768)

// Auth Store
const authStore = useAuthStore()

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
    
    // Guardar tokens y decodificar JWT usando authStore
    if (response && response.length > 0) {
      const loginData = response[0]; // API.handleResponse retorna array
      
      if (loginData.access) {
        // Usar authStore para guardar tokens y decodificar info del usuario
        // Pasamos tanto access como refresh para asegurar compatibilidad con móvil
        const loginSuccess = authStore.login(loginData.access, loginData.refresh);
        
        if (loginSuccess) {
          console.log('💾 Tokens guardados y usuario autenticado');
          console.log('👤 Usuario:', authStore.username);
          if (loginData.refresh) {
            console.log('🔄 Refresh token también guardado en localStorage');
          }
          
          // Fetch user profile data after successful login
          authStore.fetchUserProfile().catch(err => {
            console.warn('⚠️ Could not fetch user profile:', err);
          });
        } else {
          console.error('❌ Error procesando token');
          error.value = 'Error procesando autenticación';
          return;
        }
      }
      
      if (loginData.refresh) {
        // El refresh se maneja por cookies, pero podemos loggearlo
        console.log('🔄 Refresh token recibido (manejado por cookies)');
      }
    }
    
    success.value = '¡Login exitoso! Redirigiendo...'

    // Register push notifications before redirect (shows browser permission prompt)
    await registerPush()

    // Redirigir según el estado del usuario
    setTimeout(() => {
      // 1. Verificar si necesita configurar tenant
      if (authStore.needsTenantSetup) {
        console.log('⚠️ Usuario sin tenant - Redirigiendo a configuración');
        router.push('/tenant-setup');
        return;
      }
      
      // 2. Si es admin o superuser, ir a tenants
      if (authStore.isSuperUser || authStore.isAdmin) {
        router.push('/tenants');
      } else {
        // 3. Usuarios normales van a home
        router.push('/home');
      }
    }, 500);

    // Verificar cookies después del auth
    setTimeout(checkCookies, 1000)

  } catch (err) {
    console.error('❌ Error en auth:', err)
    console.error('Error completo:', {
      message: err.message,
      name: err.name,
      stack: err.stack
    })
    
    // Mensaje más descriptivo según el tipo de error
    if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
      error.value = '❌ No se puede conectar con el servidor. Verifica que el backend esté corriendo en http://localhost:8000'
    } else if (err.message.includes('CORS')) {
      error.value = '❌ Error de CORS. Verifica la configuración del backend'
    } else {
      error.value = `❌ Error: ${err.message}`
    }
  } finally {
    loading.value = false
  }
}

// Handler for Enter key inside the form: ignore textareas, otherwise submit
const onFormEnter = (e) => {
  const tag = e?.target?.tagName?.toLowerCase?.() || ''
  if (tag === 'textarea') return // don't submit when typing in multiline fields
  // prevent submitting when button disabled
  if (loading.value || !credentials.value.username || !credentials.value.password) return
  handleLogin()
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
    
    // Limpiar tokens y estado usando el store
    authStore.logout()
    
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
.google-divider {
  display: flex;
  align-items: center;
  margin: 1rem 0 0.5rem;
  color: #888;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.google-divider::before,
.google-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(0, 0, 0, 0.15);
  margin: 0 0.75rem;
}
</style>


