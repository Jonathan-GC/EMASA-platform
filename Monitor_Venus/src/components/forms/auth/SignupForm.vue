<template>
  <div class="login-container">
    <ion-card class="form-card">
      <ion-card-header class="text-center">
        <ion-card-title>¡Bienvenido a bordo!</ion-card-title>
        <ion-card-subtitle>completa el formulario para registrarte en monitor</ion-card-subtitle>
      </ion-card-header>

      <ion-card-content>
        <!-- Loading state -->
        <div v-if="loading" class="loading-container">
          <ion-spinner name="crescent"></ion-spinner>
          <p>Cargando...</p>
        </div>

        <!-- Login form -->
        <div v-else>
          <ion-item class="custom">
            <div class="flex">
              <div class="flex-2 mr-2 !pl-0 !pr-0">
                <ion-label position="stacked" class="!mb-2">Nombre</ion-label>
              <ion-input
                v-model="credentials.name"
                type="text"
                placeholder="Fulano"
                :disabled="loading"
                class="custom"
                fill="solid"

              ></ion-input>
              </div>
              <div class="flex-2 ml-2">
            <ion-label position="stacked" class="!mb-2">Apellido</ion-label>
            <ion-input
                v-model="credentials.last_name"
                type="text"
                placeholder="Detal"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            ></ion-input>
              </div>
            </div>
          </ion-item>

          <ion-item class="custom">
            <div>
                <ion-label position="stacked" class="!mb-2">Correo</ion-label>
                <ion-input
                    v-model="credentials.email"
                    type="text"
                    placeholder="ejemplo@mail.com"
                    :disabled="loading"
                    class="bg-zinc-300 rounded-md custom"
                    fill="solid"
                ></ion-input>
              </div>
          </ion-item>
          
          
          <ion-item class="custom">
            <div class="flex">
              <div class="flex-0 mr-2">
                <ion-label position="stacked" class="!mb-2">Indicativo</ion-label>
                <ModalSelector
                  v-model="selectedCountryCode"
                  :options="countries"
                  :value-field="'phoneCode'"
                  :display-field="country => `${country.phoneCode}`"
                  :search-fields="['name', 'phoneCode']"
                  title="Seleccionar Indicativo"
                  placeholder="Selecciona un indicativo"
                  search-placeholder="Buscar país..."
                  :disabled="loading"
                >
                  <template #display="{ selected }">
                    <span :class="`fi fi-${selected?.code.toLowerCase()}`" class="flag-icon"></span>
                    <span>{{ selected?.phoneCode }}</span>
                  </template>
                  
                  <template #option="{ option }">
                    <span :class="`fi fi-${option.code.toLowerCase()}`" class="flag-icon" slot="start"></span>
                    <ion-label>{{ option.name }} ({{ option.phoneCode }})</ion-label>
                  </template>
                </ModalSelector>
              </div>
              <div class="flex-2 ml-2">
                <ion-label position="stacked" class="!mb-2">Teléfono</ion-label>
                <ion-input
                    v-model="credentials.phone.number"
                    type="tel"
                    placeholder="000000000"
                    :disabled="loading"
                    class="bg-zinc-300 rounded-md custom"
                    fill="solid"
                ></ion-input>
              </div>
            </div>
          </ion-item>

           <div class="flex">
          <!-- Country Selection -->
          <ion-item class="custom flex-2 mr-2 !pl-0 !pr-0">
            <ion-label position="stacked" class="!mb-2">País</ion-label>
            <ModalSelector
              v-model="address.country"
              :options="countries"
              :value-field="'name'"
              :display-field="'name'"
              :search-fields="['name']"
              title="Selecciona tu país"
              placeholder=" -"
              search-placeholder="Buscar país..."
              :disabled="loading"
            >
              <template #option="{ option }">
                <span :class="`fi fi-${option.code.toLowerCase()}`" class="flag-icon" slot="start"></span>
                <ion-label>{{ option.name }}</ion-label>
              </template>
            </ModalSelector>
          </ion-item>

          <!-- State Selection -->
          <ion-item class="custom flex-2 mr-2 !pl-0 !pr-0">
            <ion-label position="stacked" class="!mb-2">Provincia</ion-label>
            <ModalSelector
              v-model="address.state"
              :options="availableStates"
              :display-field="state => state"
              title="Selecciona tu provincia"
              placeholder=" -"
              search-placeholder="Buscar provincia..."
              :disabled="loading || !address.country"
            />
          </ion-item>

          <!-- City Selection -->
          <ion-item class="custom flex-2 !pl-0 !pr-0">
            <ion-label position="stacked" class="!mb-2">Ciudad</ion-label>
            <ModalSelector
              v-model="address.city"
              :options="availableCities"
              :display-field="city => city"
              title="Selecciona tu ciudad"
              placeholder=" -"
              search-placeholder="Buscar ciudad..."
              :disabled="loading || !address.country || !address.state"
            />
          </ion-item>
          </div>

          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Dirección</ion-label>
            <ion-input
                v-model="credentials.address.street"
                type="text"
                placeholder="Calle Falsa #12-3"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            ></ion-input>
          </ion-item>

          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Usuario</ion-label>
            <ion-input
                v-model="credentials.username"
                type="text"
                placeholder="nombre.usuario"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            >
              
            </ion-input>
          </ion-item>

          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Constraseña</ion-label>
            <ion-input
                v-model="credentials.password"
                :type="passwordInputType"
                placeholder="*****"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            >
              <ion-button
                fill="clear"
                slot="end"
                @click="togglePasswordVisibility"
                class="password-toggle-btn rounded-full"
              >
                <ion-icon
                  :icon="showPassword ? icons.eyeOff : icons.eye"
                  color="medium"
                  slot="icon-only"
                ></ion-icon>
              </ion-button>
            </ion-input>
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
              Registrar
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
            <p class="text-center">¿Ya tienes una cuenta? <router-link :to="paths.LOGIN">Ingresa aquí</router-link></p>
          </div>
        </div>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, inject, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import API from '@utils/api/index.js'
import {paths}  from '@/plugins/router/paths.js'
import { countries } from '@/data/countries.js'
import { cities } from '@/data/cities.js'
import ModalSelector from '@/components/ui/ModalSelector.vue'


// Router instance
const router = useRouter()

// Iconos desde el plugin
const icons = inject('icons', {})

// Estado reactivo
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const cookieInfo = ref(null)
const showPassword = ref(false)
const selectedCountryCode = ref('+57') // Default to Colombia

// Credenciales del usuario
const credentials = ref({
  username: '',
  password: '',
  name: '',
  last_name: '',
  email: '',
  phone: {
    countryCode: selectedCountryCode.value,
    number: ''
  },
  address: {
    country: '',
    state: '',
    city: '',
    street: ''
  }
})

// Watcher para mantener sincronizado el countryCode
watch(selectedCountryCode, (newCode) => {
  credentials.value.phone.countryCode = newCode
})

// Dirección reactiva para CountryRegionSelect
const address = ref({
  country: '',
  state: '',
  city: ''
})

// Watchers para sincronizar address con credentials.address
watch(() => address.value.country, (newVal) => {
  credentials.value.address.country = newVal
  // Reset dependent fields when country changes
  address.value.state = ''
  address.value.city = ''
})
watch(() => address.value.state, (newVal) => {
  credentials.value.address.state = newVal
  // Reset city when state changes
  address.value.city = ''
})
watch(() => address.value.city, (newVal) => {
  credentials.value.address.city = newVal
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

// Computed property for password input type
const passwordInputType = computed(() => showPassword.value ? 'text' : 'password')

// Computed property for available states based on selected country
const availableStates = computed(() => {
  const countryName = address.value.country

  if (!countryName) return []

  // Find the country code from the country name
  const country = countries.find(c => c.name === countryName)
  if (!country) return []

  const countryCode = country.code

  // Get states for the country
  const countryCities = cities[countryCode]
  if (!countryCities) return []

  return Object.keys(countryCities)
})

// Computed property for available cities based on selected country and state
const availableCities = computed(() => {
  const countryName = address.value.country
  const stateName = address.value.state

  if (!countryName || !stateName) return []

  // Find the country code from the country name
  const country = countries.find(c => c.name === countryName)

  if (!country) return []

  const countryCode = country.code

  // Get cities for the country and state
  const countryCities = cities[countryCode]

  if (!countryCities) return []

  const stateCities = countryCities[stateName] || []

  return stateCities
})

// Función para limpiar mensajes
const clearMessages = () => {
  error.value = null
  success.value = null
}

// Función para alternar visibilidad de contraseña
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
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

// Función principal de registro
const handleLogin = async () => {
  if (!credentials.value.username || !credentials.value.password || !credentials.value.name || !credentials.value.email || !credentials.value.phone.number || !credentials.value.address.country || !credentials.value.address.city) {
    error.value = 'Por favor completa todos los campos requeridos'
    return
  }

  loading.value = true
  clearMessages()

  try {
    console.log('🔑 Intentando registro con:', {
      username: credentials.value.username,
      email: credentials.value.email,
      name: credentials.value.name,
      address: credentials.value.address,
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

    // Realizar registro con CSRF token
    const response = await API.post(API.REGISTER, credentials.value, headers)

    console.log('✅ Registro exitoso:', response)

    success.value = '¡Registro exitoso! Revisa tu email para confirmar.'

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
  max-width: 700px;
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

/* Country flag fallback for Windows */
.country-flag {
  font-family: 'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', sans-serif;
  font-size: 1.2em;
  margin-right: 4px;
}

/* Flag icon styling */
.flag-icon {
  width: 20px;
  height: 15px;
  display: inline-block;
  margin-right: 8px;
  vertical-align: middle;
  border-radius: 2px;
}

/* Country select label styling */
.country-select [slot="label"] {
  display: flex;
  align-items: center;
  gap: 4px;
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
