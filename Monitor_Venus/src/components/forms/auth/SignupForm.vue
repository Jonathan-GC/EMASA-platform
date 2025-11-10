<template>
  <div class="signup-container">
    <ion-card class="form-container bg-amber-700/0 ">
      <ion-card-header class="text-center">
        <ion-card-title style="--color:white">¡Bienvenido a bordo!</ion-card-title>
        <ion-card-subtitle style="--color:var(--color-zinc-300)">completa el formulario para registrarte en monitor</ion-card-subtitle>
        
        <!-- Progress Indicator -->
        <div class="progress-container">
          <div class="progress-steps">
            <div 
              v-for="(step, index) in steps" 
              :key="index"
              class="step-indicator"
              :class="{ 
                active: currentStep === index + 1,
                completed: currentStep > index + 1 
              }"
            >
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-label">{{ step.label }}</div>
            </div>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }"
            ></div>
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
            <hr class="divider"/>
          
          <!-- Name and Last Name -->
          <ion-item class="custom">
            <div :class="isMobile ? 'flex-column' : 'flex'">
              <div :class="isMobile ? 'full-width mb-4' : 'flex-2 mr-2 !pl-0 !pr-0'">
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
              <div :class="isMobile ? 'full-width' : 'flex-2 ml-2'">
                <ion-label position="stacked" class="!mb-2">Apellido</ion-label>
                <ion-input
                  v-model="credentials.last_name"
                  type="text"
                  placeholder="Detal"
                  :disabled="loading"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </div>
            </div>
          </ion-item>

          <!-- Email -->
          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Correo</ion-label>
            <ion-input
              v-model="credentials.email"
              type="email"
              placeholder="ejemplo@mail.com"
              :disabled="loading"
              class="custom"
              fill="solid"
            ></ion-input>
          </ion-item>
          
          <!-- Phone -->
          <ion-item class="custom">
            <div :class="isMobile ? 'flex-column' : 'flex'">
              <div :class="isMobile ? 'full-width mb-4' : 'flex-0 mr-2'">
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
              <div :class="isMobile ? 'full-width' : 'flex-2 ml-2'">
                <ion-label position="stacked" class="!mb-2">Teléfono</ion-label>
                <ion-input
                  v-model="credentials.phone"
                  type="tel"
                  placeholder="000000000"
                  :disabled="loading"
                  class="custom"
                  fill="solid"
                ></ion-input>
              </div>
            </div>
          </ion-item>

          <!-- Address -->
          <div :class="isMobile ? 'flex-column' : 'flex'">
            <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
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

            <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-2 mr-2 !pl-0 !pr-0'">
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

            <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2 !pl-0 !pr-0'">
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

          <div :class="isMobile ? 'flex-column' : 'flex'">
          <ion-item :class="isMobile ? 'custom full-width mb-4' : 'custom flex-3 mr-2'">
            <ion-label position="stacked" class="!mb-2">Dirección</ion-label>
            <ion-input
                v-model="credentials.address.address"
                type="text"
                placeholder="Calle Falsa #12-3"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            ></ion-input>
          </ion-item>
            
          <ion-item :class="isMobile ? 'custom full-width' : 'custom flex-2'">
            <ion-label position="stacked" class="!mb-2">Código Postal</ion-label>
            <ion-input
                v-model="credentials.address.zip_code"
                type="text"
                placeholder="000000"
                :disabled="loading"
                class="bg-zinc-300 rounded-md custom"
                fill="solid"
            ></ion-input>
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
          <hr class="divider"/>
          
          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Usuario</ion-label>
            <ion-input
              v-model="credentials.username"
              type="text"
              placeholder="nombre.usuario"
              :disabled="loading"
              class="custom"
              fill="solid"
            ></ion-input>
          </ion-item>

          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Contraseña</ion-label>
            <ion-input
              v-model="credentials.password"
              :type="passwordInputType"
              placeholder="*****"
              :disabled="loading"
              class="custom"
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
          <ion-item class="custom">
            <ion-label position="stacked" class="!mb-2">Confirma tu contraseña</ion-label>
            <ion-input
              v-model="credentials.confirm_password"
              :type="passwordInputType"
              placeholder="*****"
              :disabled="loading"
              class="custom"
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
          </ion-card-content>
          </ion-card>
        </div>

        <!-- Step 3: Profile Picture -->
        <div v-else-if="currentStep === 3" class="step-content">
         <ion-card class="form-card">
         <h1 class="step-title">Foto de Perfil</h1>
         <hr class="divider"/>
          
          <div class="profile-picture-section">
            <div class="image-upload-container">
              <div class="image-preview" @click="triggerFileInput">
                <img 
                  v-if="profileImage" 
                  :src="profileImage" 
                  alt="Profile preview" 
                  class="profile-image"
                />
                <div v-else class="image-placeholder">
                  <ion-icon :icon="icons.camera" size="large"></ion-icon>
                  <p>Haz clic para seleccionar una imagen</p>
                </div>
              </div>
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                @change="handleImageUpload"
                style="display: none"
              />
            </div>
            
            <div class="image-actions">
              <ion-button 
                v-if="profileImage" 
                fill="outline" 
                color="danger" 
                @click="removeImage"
              >
                <ion-icon :icon="icons.delete" slot="start"></ion-icon>
                Remover
              </ion-button>
            </div>
          </div>
          </ion-card>
        </div>

        <!-- Navigation Buttons -->
        <div class="navigation-buttons">
          <ion-button
            v-if="currentStep > 1"
            fill="outline"
            color="danger"
            @click="previousStep"
            :disabled="loading"
          >
            <ion-icon :icon="icons.arrowBack" slot="start"></ion-icon>
            Anterior
          </ion-button>
          
          <ion-button
            v-if="currentStep < steps.length"
            @click="nextStep"
            :disabled="!canProceedToNextStep"
            :loading="loading"
            class="custom next-button"
          >
            Siguiente
            <ion-icon :icon="icons.arrowForward" slot="end"></ion-icon>
          </ion-button>
          
          <ion-button
            v-else
            expand="block"
            color="amber-600"
            class="bg-amber-600"
            @click="handleRegistration"
            :disabled="!canSubmit"
            :loading="loading"
          >
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
import { useResponsiveView } from '@/composables/useResponsiveView.js'

// Router instance
const router = useRouter()

// Responsive view
const { isMobile } = useResponsiveView(480)

// Iconos desde el plugin
const icons = inject('icons', {})

// Multi-step state
const currentStep = ref(1)
const steps = [
  { label: 'Personal', required: ['name', 'last_name', 'email', 'phone', 'address.country', 'address.city', 'address.address'] },
  { label: 'Cuenta', required: ['username', 'password'] },
  { label: 'Foto', required: [] } // Profile picture is optional
]

// Estado reactivo
const loading = ref(false)
const error = ref(null)
const success = ref(null)
const showPassword = ref(false)
const selectedCountryCode = ref('+57')
const profileImage = ref(null)
const fileInput = ref(null)

// Credenciales del usuario
const credentials = ref({
  username: '',
  password: '',
  name: '',
  last_name: '',
  email: '',
  phone_code: selectedCountryCode.value,
  phone: '',
  address: {
    country: '',
    state: '',
    city: '',
    address: '',
    zip_code: ''
  }
})

// Dirección reactiva para CountryRegionSelect
const address = ref({
  country: '',
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

// Watchers para sincronizar address con credentials.address
watch(() => address.value.country, (newVal) => {
  credentials.value.address.country = newVal
  address.value.state = ''
  address.value.city = ''
})
watch(() => address.value.state, (newVal) => {
  credentials.value.address.state = newVal
  address.value.city = ''
})
watch(() => address.value.city, (newVal) => {
  credentials.value.address.city = newVal
})

// Computed properties
const passwordInputType = computed(() => showPassword.value ? 'text' : 'password')

const availableStates = computed(() => {
  const countryName = address.value.country
  if (!countryName) return []
  const country = countries.find(c => c.name === countryName)
  if (!country) return []
  const countryCode = country.code
  const countryCities = cities[countryCode]
  if (!countryCities) return []
  return Object.keys(countryCities)
})

const availableCities = computed(() => {
  const countryName = address.value.country
  const stateName = address.value.state
  if (!countryName || !stateName) return []
  const country = countries.find(c => c.name === countryName)
  if (!country) return []
  const countryCode = country.code
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

// Profile image functions
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      profileImage.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const removeImage = () => {
  profileImage.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
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

    // Get CSRF token if needed
    let csrfToken = getCookieValue('csrftoken')
    if (!csrfToken) {
      console.log('🛡️ No hay CSRF token, obteniendo uno...')
      await getCsrfToken()
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    const headers = getHeadersWithCSRF()

    // Prepare form data with image if present
    const formData = { ...credentials.value }
    if (profileImage.value) {
      formData.profile_image = profileImage.value
    }

    const response = await API.post(API.REGISTER, formData, headers)

    console.log('✅ Registro exitoso:', response)
    success.value = '¡Registro exitoso! Revisa tu email para confirmar.'

    setTimeout(() => {
      router.push('/tenants')
    }, 500)

  } catch (err) {
    console.error('❌ Error en registro:', err)
    error.value = `Error: ${err.message}`
  } finally {
    loading.value = false
  }
}

// Other functions remain the same...
</script>

