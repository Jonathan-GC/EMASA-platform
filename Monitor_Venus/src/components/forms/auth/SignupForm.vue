<template>
  <div class="signup-container">
    <ion-card class="form-container bg-amber-700/0">
      <div v-if="registrationComplete" class="flex flex-col items-center">
        <!-- Registration Complete State -->
        <ion-card  class="success-card">
          <ion-card-header class="text-center">
            <div class="success-icon">
              <ion-icon :icon="checkmarkCircle" class="success-checkmark"></ion-icon>
            </div>
            <ion-card-title>¡Registro exitoso!</ion-card-title>
          </ion-card-header>

          <ion-card-content class="text-center">
            <p class="verification-message">
              Hemos enviado un enlace de verificación a<br />
              <strong>{{ registeredEmail }}</strong>
            </p>
            <p class="verification-instructions" color="secondary
          ">
              Por favor revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta.
            </p>

            <div class="action-buttons">
              <ion-button expand="block" fill="solid" color="dark" shape="round" @click="handleResendVerification"
                :disabled="resendLoading || resendCooldown > 0" class="resend-button">
                <ion-icon :icon="icons.mail" slot="start"></ion-icon>
                {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : 'Reenviar correo' }}
              </ion-button>
            </div>

            <!-- Resend Messages -->
            <div v-if="resendSuccess" class="resend-success">
              <ion-icon :icon="icons.checkmarkCircle" color="success"></ion-icon>
              {{ resendSuccess }}
            </div>

            <div v-if="resendError" class="resend-error">
              <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
              {{ resendError }}
            </div>
          </ion-card-content>
        </ion-card>
      </div>

      <!-- Normal Registration Flow -->
      <template v-else>
        <ion-card-header class="text-center">
          <ion-card-title style="--color:white">¡Bienvenido a bordo!</ion-card-title>
          <ion-card-subtitle style="--color:var(--color-zinc-300)">completa el formulario para registrarte en
            monitor</ion-card-subtitle>

          <!-- Progress Indicator -->
          <div class="progress-container">
            <div class="progress-steps">
              <div v-for="(step, index) in steps" :key="index" class="step-indicator" :class="{ 
                  active: currentStep === index + 1,
                  completed: currentStep > index + 1 
                }">
                <div class="step-number">{{ index + 1 }}</div>
                <div class="step-label">{{ step.label }}</div>
              </div>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }"></div>
            </div>
          </div>
        </ion-card-header>

        <ion-card-content class="signup-card-content">
          <!-- Loading state -->
          <div v-if="loading" class="loading-container">
            <ion-spinner name="crescent"></ion-spinner>
            <p>Cargando...</p>
          </div>

          <!-- Step 1: Personal Data -->
          <div v-else-if="currentStep === 1" class="step-content">
            <ion-card class="form-card">
              <ion-card-content>
                <h1 class="step-title">Datos Personales</h1>
                <hr class="divider" />

                <!-- Name and Last Name -->
                <ion-item class="custom">
                  <div :class="isMobile ? 'flex-column' : 'flex'">
                    <div :class="isMobile ? 'full-width mb-4' : 'flex-2 mr-2 !pl-0 !pr-0'">
                      <ion-label position="stacked" class="!mb-2">Nombre</ion-label>
                      <ion-input v-model="credentials.name" type="text" placeholder="Fulano" :disabled="loading"
                        class="custom" fill="solid"></ion-input>
                    </div>
                    <div :class="isMobile ? 'full-width' : 'flex-2 ml-2'">
                      <ion-label position="stacked" class="!mb-2">Apellido</ion-label>
                      <ion-input v-model="credentials.last_name" type="text" placeholder="Detal" :disabled="loading"
                        class="custom" fill="solid"></ion-input>
                    </div>
                  </div>
                </ion-item>

                <!-- Email -->
                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Correo</ion-label>
                  <ion-input v-model="credentials.email" type="email" placeholder="ejemplo@mail.com" :disabled="loading"
                    class="custom" fill="solid"></ion-input>
                </ion-item>

                <!-- Phone -->
                <ion-item class="custom">
                  <div :class="isMobile ? 'flex-column' : 'flex'">
                    <div :class="isMobile ? 'full-width mb-4' : 'flex-0 mr-2'">
                      <ion-label position="stacked" class="!mb-2">Indicativo</ion-label>
                      <ModalSelector v-model="selectedCountryCode" :options="countries" :value-field="'phoneCode'"
                        :display-field="country => `${country.phoneCode}`" :search-fields="['name', 'phoneCode']"
                        title="Seleccionar Indicativo" placeholder="Selecciona un indicativo"
                        search-placeholder="Buscar país..." :disabled="loading">
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
                    <div :class="isMobile ? 'full-width' : 'flex-2 ml-2'">
                      <ion-label position="stacked" class="!mb-2">Teléfono</ion-label>
                      <ion-input v-model="credentials.phone" type="tel" placeholder="000000000" :disabled="loading"
                        class="custom" fill="solid"></ion-input>
                    </div>
                  </div>
                </ion-item>

                <!-- Address -->
                <div :class="isMobile ? 'flex-column' : 'flex'">
                  <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
                    <ion-label position="stacked" class="!mb-2">País</ion-label>
                    <ModalSelector v-model="country" :options="countries" :value-field="'name'" :display-field="'name'"
                      :search-fields="['name']" title="Selecciona tu país" placeholder=" -"
                      search-placeholder="Buscar país..." :disabled="loading">
                      <template #option="{ option }">
                        <span :class="`fi fi-${option.code.toLowerCase()}`" class="flag-icon" slot="start"></span>
                        <ion-label>{{ option.name }}</ion-label>
                      </template>
                    </ModalSelector>
                  </ion-item>

                  <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
                    <ion-label position="stacked" class="!mb-2">Provincia</ion-label>
                    <ModalSelector v-model="address.state" :options="availableStates" :display-field="state => state"
                      title="Selecciona tu provincia" placeholder=" -" search-placeholder="Buscar provincia..."
                      :disabled="loading || !country" />
                  </ion-item>

                  <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2 !pl-0 !pr-0'">
                    <ion-label position="stacked" class="!mb-2">Ciudad</ion-label>
                    <ModalSelector v-model="address.city" :options="availableCities" :display-field="city => city"
                      title="Selecciona tu ciudad" placeholder=" -" search-placeholder="Buscar ciudad..."
                      :disabled="loading || !country || !address.state" />
                  </ion-item>
                </div>

                <div :class="isMobile ? 'flex-column' : 'flex'">
                  <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-3 mr-2'">
                    <ion-label position="stacked" class="!mb-2">Dirección</ion-label>
                    <ion-input v-model="credentials.address.address" type="text" placeholder="Calle Falsa #12-3"
                      :disabled="loading" class="bg-zinc-300 rounded-md custom" fill="solid"></ion-input>
                  </ion-item>

                  <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2'">
                    <ion-label position="stacked" class="!mb-2">Código Postal</ion-label>
                    <ion-input v-model="credentials.address.zip_code" type="text" placeholder="000000"
                      :disabled="loading" class="bg-zinc-300 rounded-md custom" fill="solid"></ion-input>
                  </ion-item>
                </div>
              </ion-card-content>
            </ion-card>
          </div>

          <!-- Step 2: Account Details -->
          <div v-else-if="currentStep === 2" class="step-content">
            <ion-card class="form-card">
              <ion-card-content>
                <h1 class="step-title">Detalles de Cuenta</h1>
                <hr class="divider" />

                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Usuario</ion-label>
                  <ion-input v-model="credentials.username" type="text" placeholder="nombre.usuario" :disabled="loading"
                    class="custom" fill="solid"></ion-input>
                </ion-item>

                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Contraseña</ion-label>
                  <ion-input v-model="credentials.password" :type="passwordInputType" placeholder="*****"
                    :disabled="loading" class="custom" fill="solid">
                    <ion-button fill="clear" slot="end" @click="togglePasswordVisibility"
                      class="password-toggle-btn rounded-full">
                      <ion-icon :icon="showPassword ? icons.eyeOff : icons.eye" color="medium"
                        slot="icon-only"></ion-icon>
                    </ion-button>
                  </ion-input>
                </ion-item>
                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Confirma tu contraseña</ion-label>
                  <ion-input v-model="credentials.confirm_password" :type="passwordInputType" placeholder="*****"
                    :disabled="loading" class="custom" fill="solid">
                    <ion-button fill="clear" slot="end" @click="togglePasswordVisibility"
                      class="password-toggle-btn rounded-full">
                      <ion-icon :icon="showPassword ? icons.eyeOff : icons.eye" color="medium"
                        slot="icon-only"></ion-icon>
                    </ion-button>
                  </ion-input>
                </ion-item>
              </ion-card-content>
            </ion-card>
          </div>

          <!-- Step 3: Profile Picture -->
          <div v-else-if="currentStep === 3" class="step-content">
            <ion-card class="form-card">
              <h1 class="step-title">Foto de Perfil</h1>
              <hr class="divider" />

              <div class="profile-picture-section">
                <ImageUpload ref="imageUploadRef" v-model="profileImage" :icon="icons.camera"
                  placeholder-text="Haz clic para seleccionar una imagen" alt="Profile preview"
                  remove-button-text="Remover" :max-size="5 * 1024 * 1024" @change="handleImageChange"
                  @error="handleImageError" />
              </div>
            </ion-card>
          </div>

          <!-- Navigation Buttons -->
          <div class="navigation-buttons">
            <ion-button v-if="currentStep > 1" fill="outline" color="danger" @click="previousStep" :disabled="loading">
              <ion-icon :icon="icons.arrowBack" slot="start"></ion-icon>
              Anterior
            </ion-button>

            <ion-button v-if="currentStep < steps.length" @click="nextStep" :disabled="!canProceedToNextStep"
              :loading="loading" class="custom next-button">
              Siguiente
              <ion-icon :icon="icons.arrowForward" slot="end"></ion-icon>
            </ion-button>

            <ion-button v-else expand="block" color="amber-600" class="bg-amber-600" @click="handleRegistration"
              :disabled="!canSubmit" :loading="loading">
              <ion-icon :icon="icons.key" slot="start"></ion-icon>
              Registrar
            </ion-button>
          </div>

          <!-- Error/Success Messages -->
          <div v-if="error" class="error-message bg-zinc-100">
            <ion-icon :icon="icons.alertCircle" color="danger"></ion-icon>
            {{ error }}
          </div>

          <div v-if="success" class="success-message">
            <ion-icon :icon="icons.checkmarkCircle" color="success"></ion-icon>
            {{ success }}
          </div>
        </ion-card-content>
      </template>
    </ion-card>
  </div>
</template>

<script setup>
import { ref, inject, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import API from '@/utils/api/api.js'
import { paths } from '@/plugins/router/paths.js'
import { countries } from '@/data/countries.js'
import { cities } from '@/data/cities.js'
import ModalSelector from '@/components/ui/ModalSelector.vue'
import ImageUpload from '@/components/common/ImageUpload.vue'
import { useResponsiveView } from '@/composables/useResponsiveView.js'
import { checkmarkCircle } from 'ionicons/icons'

// Router instance
const router = useRouter()

// Responsive view
const { isMobile } = useResponsiveView(480)

// Iconos desde el plugin
const icons = inject('icons', {})

// Multi-step state
const currentStep = ref(1)
const steps = [
  { label: 'Personal', required: ['name', 'last_name', 'email', 'phone', 'country', 'address.city', 'address.address'] },
  { label: 'Cuenta', required: ['username', 'password'] },
  { label: 'Foto', required: [] } // Profile picture is optional
]

// Estado reactivo
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const registrationComplete = ref(false)
const registeredEmail = ref('')
const resendLoading = ref(false)
const resendSuccess = ref(null)
const resendError = ref(null)
const resendCooldown = ref(0)
const showPassword = ref(false)
const selectedCountryCode = ref('+57')
const profileImage = ref(null)
const imageUploadRef = ref(null)

// Credenciales del usuario
const credentials = ref({
  username: '',
  password: '',
  confirm_password: '',
  name: '',
  last_name: '',
  country: '',
  email: '',
  phone_code: selectedCountryCode.value,
  phone: '',
  address: {
    state: '',
    city: '',
    address: '',
    zip_code: ''
  }
})

// Reactive variables for country/state/city selection
const country = ref('')
const address = ref({
  state: '',
  city: ''
})

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

// Watcher para mantener sincronizado el countryCode
watch(selectedCountryCode, (newCode) => {
  credentials.value.phone_code = newCode
})

// Watchers to sync country/state/city with credentials
watch(country, (newVal) => {
  credentials.value.country = newVal
  address.value.state = ''
  address.value.city = ''
  credentials.value.address.state = ''
  credentials.value.address.city = ''
})

watch(() => address.value.state, (newVal) => {
  credentials.value.address.state = newVal
  address.value.city = ''
  credentials.value.address.city = ''
})

watch(() => address.value.city, (newVal) => {
  credentials.value.address.city = newVal
})

// Computed properties
const passwordInputType = computed(() => showPassword.value ? 'text' : 'password')

const availableStates = computed(() => {
  const countryName = country.value
  if (!countryName) return []
  const selectedCountry = countries.find(c => c.name === countryName)
  if (!selectedCountry) return []
  const countryCode = selectedCountry.code
  const countryCities = cities[countryCode]
  if (!countryCities) return []
  return Object.keys(countryCities)
})

const availableCities = computed(() => {
  const countryName = country.value
  const stateName = address.value.state
  if (!countryName || !stateName) return []
  const selectedCountry = countries.find(c => c.name === countryName)
  if (!selectedCountry) return []
  const countryCode = selectedCountry.code
  const countryCities = cities[countryCode]
  if (!countryCities) return []
  const stateCities = countryCities[stateName] || []
  return stateCities
})

const canProceedToNextStep = computed(() => {
  const currentStepData = steps[currentStep.value - 1]
  return currentStepData.required.every(field => {
    const keys = field.split('.')
    let value = credentials.value
    for (const key of keys) {
      value = value[key]
    }
    return value && value.toString().trim() !== ''
  })
})

const canSubmit = computed(() => {
  return canProceedToNextStep.value
})

// Fetch CSRF token on component mount
onMounted(async () => {
  console.log('🔧 SignupForm mounted - fetching CSRF token')
  try {
    console.log('🔐 Fetching CSRF token...')
    await API.get(API.CSRF_TOKEN)
    console.log('✅ CSRF token obtained and stored in cookies')
  } catch (error) {
    console.error('❌ Failed to fetch CSRF token:', error)
    // Don't set error.value here to avoid blocking the form UI
    // The CSRF will be fetched again when needed in handleRegistration
  }
})

// Step navigation functions
const nextStep = () => {
  if (canProceedToNextStep.value && currentStep.value < steps.length) {
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Profile image functions - now handled by ImageUpload component
const handleImageChange = (fileInfo) => {
  console.log('📸 Image uploaded:', fileInfo)
  // The profileImage is automatically updated via v-model
  // Additional logic can be added here if needed
}

const handleImageError = (errorMessage) => {
  console.error('❌ Image upload error:', errorMessage)
  error.value = errorMessage
}

const getCookieValue = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

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

// Add this function before handleRegistration
const clearMessages = () => {
  error.value = null
  success.value = null
}

const getHeadersWithCSRF = () => {
  const csrfToken = getCookieValue('csrftoken')
  return {
    'X-CSRFToken': csrfToken,
    'Content-Type': 'application/json'
  }
}
// Other functions (togglePasswordVisibility, getCookieValue, etc.) remain the same...

// Updated registration function
const handleRegistration = async () => {
  if (!canSubmit.value) {
    error.value = 'Por favor completa todos los campos requeridos'
    return
  }

  loading.value = true

  try {
    console.log('🔑 Intentando registro con:', {
      ...credentials.value,
      profileImage: profileImage.value ? 'Present' : 'Not present'
    })

    // Get CSRF token if needed (fallback in case onMounted failed)
    let csrfToken = getCookieValue('csrftoken')
    if (!csrfToken) {
      console.log('🛡️ No hay CSRF token, obteniendo uno...')
      await getCsrfToken()
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    // Get file info from ImageUpload component
    const fileInfo = imageUploadRef.value?.getFileInfo()

    // Prepare payload - use FormData if there's a file, otherwise JSON
    let payload
    let headers = getHeadersWithCSRF()

    if (fileInfo?.file) {
      // Has file - use FormData for file upload
      console.log('📦 Using FormData for file upload')
      const formData = new FormData()

      // Add user fields (exact structure expected by backend)
      formData.append('username', credentials.value.username)
      formData.append('password', credentials.value.password)
      formData.append('confirm_password', credentials.value.confirm_password)
      formData.append('name', credentials.value.name)
      formData.append('last_name', credentials.value.last_name)
      formData.append('email', credentials.value.email)
      formData.append('country', credentials.value.country)
      formData.append('phone_code', credentials.value.phone_code)
      formData.append('phone', credentials.value.phone)

      // Add nested address object as JSON string
      formData.append('address', JSON.stringify({
        address: credentials.value.address.address,
        city: credentials.value.address.city,
        state: credentials.value.address.state,
        zip_code: credentials.value.address.zip_code
      }))

      // Add profile image file
      formData.append('img', fileInfo.file)

      payload = formData

      // Remove Content-Type header - browser will set it with boundary
      delete headers['Content-Type']
    } else {
      // No file - use regular JSON
      console.log('📄 Using JSON payload (no file)')
      payload = {
        username: credentials.value.username,
        password: credentials.value.password,
        confirm_password: credentials.value.confirm_password,
        name: credentials.value.name,
        last_name: credentials.value.last_name,
        email: credentials.value.email,
        country: credentials.value.country,
        phone_code: credentials.value.phone_code,
        phone: credentials.value.phone,
        address: {
          address: credentials.value.address.address,
          city: credentials.value.address.city,
          state: credentials.value.address.state,
          zip_code: credentials.value.address.zip_code
        }
      }
    }

    const response = await API.post(API.REGISTER, payload, headers)

    console.log('✅ Registro exitoso:', response)

    // Set registration complete state
    registeredEmail.value = credentials.value.email
    registrationComplete.value = true

  } catch (err) {
    console.error('❌ Error en registro:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

const handleResendVerification = async () => {
  if (resendCooldown.value > 0) return

  resendLoading.value = true
  resendSuccess.value = null
  resendError.value = null

  try {
    await API.post(API.RESEND_VERIFICATION, { email: registeredEmail.value })

    resendSuccess.value = 'Correo de verificación reenviado exitosamente'

    // Start cooldown timer (60 seconds)
    resendCooldown.value = 60
    const timer = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)

    // Clear success message after 5 seconds
    setTimeout(() => {
      resendSuccess.value = null
    }, 5000)

  } catch (err) {
    console.error('❌ Error reenviando verificación:', err)
    resendError.value = `Error: ${err.message}`

    // Clear error message after 5 seconds
    setTimeout(() => {
      resendError.value = null
    }, 5000)
  } finally {
    resendLoading.value = false
  }
}

// Other functions remain the same...
</script>

<style scoped>
.success-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 1rem 0;
}

.success-checkmark {
  font-size: 5rem;
  color: var(--ion-color-success);
  animation: scaleIn 0.5s ease-out;
}

@keyframes scaleIn {
  0% {
    transform: scale(0);
    opacity: 0;
  }

  50% {
    transform: scale(1.1);
  }

  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.verification-message {
  font-size: 1.1rem;
  margin: 1.5rem 0 1rem;
  line-height: 1.6;
}

.verification-message strong {
  color: var(--ion-color-primary);
  font-weight: 600;
}

.verification-instructions {
  font-size: 0.95rem;
  color: var(--ion-color-medium);
  margin-bottom: 2rem;
  line-height: 1.5;
}

.action-buttons {
  margin-top: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.resend-button {
  --border-color: var(--ion-color-light);
  --color: var(--ion-color-light);
  font-weight: 500;
}

.resend-button:disabled {
  opacity: 0.5;
}

.login-button {
  --background: var(--ion-color-primary);
  --color: white;
  font-weight: 600;
}

.resend-success {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  color: var(--ion-color-success);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.resend-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  color: var(--ion-color-danger);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}
</style>
