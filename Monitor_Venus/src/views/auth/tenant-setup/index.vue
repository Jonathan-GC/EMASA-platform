<template>
  <ion-page>
    <ion-header class="ion-no-border transparent-header">
      <ion-toolbar class="transparent-toolbar">
        <ion-title class="text-neutral-50 back-button-text">Configuración Inicial</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="handleLogout">
            <ion-icon :icon="logOutOutline"></ion-icon>
            <span class="back-button-text">Cerrar Sesión</span>
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="verification-page custom">
      <div class="setup-container">
        <!-- Welcome Section -->
        <div class="welcome-section">
          <div class="icon-wrapper">
            <ion-icon :icon="businessOutline" class="main-icon"></ion-icon>
          </div>
          
          <h1 class="welcome-title" style="color:white">¡Bienvenido a Monitor!</h1>
          <p class="welcome-subtitle" style="color:var(--color-zinc-300)">
            Hola <strong>{{ authStore.username }}</strong>, 
            para comenzar necesitas crear tu organización.
          </p>
        </div>

        <!-- Info Cards -->
        <!--<div class="info-cards">
          <ion-card class="info-card">
            <ion-card-content>
              <div class="card-icon-wrapper">
                <ion-icon :icon="informationCircleOutline" class="card-icon"></ion-icon>
              </div>
              <h3>¿Qué es un Tenant?</h3>
              <p>
                Un tenant es tu espacio de trabajo aislado donde gestionarás tus dispositivos, 
                aplicaciones y datos. Es como tu propia organización dentro de la plataforma.
              </p>
            </ion-card-content>
          </ion-card>

          <ion-card class="info-card">
            <ion-card-content>
              <div class="card-icon-wrapper">
                <ion-icon :icon="shieldCheckmarkOutline" class="card-icon"></ion-icon>
              </div>
              <h3>Privacidad y Seguridad</h3>
              <p>
                Tus datos estarán completamente aislados de otros usuarios. 
                Solo tú y las personas que invites tendrán acceso a tu tenant.
              </p>
            </ion-card-content>
          </ion-card>
        </div>-->

        <!-- Create Tenant Form -->
        <ion-card class="form-card">
          <ion-card-header>
            <ion-card-title>Crear Tu Organización</ion-card-title>
            <ion-card-subtitle class="section-description !mb-1">
              <ion-icon :icon="shieldCheckmarkOutline" class="card-icon" size="small"></ion-icon>
              <span>Tus datos estarán completamente aislados de otros usuarios. 
                Solo tú y las personas que invites tendrán acceso a tu tenant.</span></ion-card-subtitle>
          </ion-card-header>
  
          

          <ion-card-content>
            <form @submit.prevent="handleCreateTenant">
              <ion-list>
                <!-- Organization Image Upload -->
                <div>
                  <ImageUpload
                    ref="imageUploadRef"
                    v-model="tenantForm.img"
                    :icon="imageOutline"
                    placeholder-text="Haz clic para seleccionar el logo"
                    alt="Organization logo"
                    remove-button-text="Remover logo"
                    :max-size="5 * 1024 * 1024"
                    :disabled="loading"
                    @change="handleImageChange"
                    @error="handleImageError"
                  />
                </div>

                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Nombre de la Organización *</ion-label>
                  <ion-input
                    v-model="tenantForm.name"
                    class="custom"
                    placeholder="Mi Empresa S.A."
                    required
                    fill="solid"
                    :disabled="loading"
                  ></ion-input>
                </ion-item>

                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">Description</ion-label>
                  <ion-textarea
                    v-model="tenantForm.description"
                    class="custom"
                    fill="solid"
                    placeholder="Describe tu organización (opcional)"
                    :disabled="loading"
                  ></ion-textarea>
                </ion-item>     
                
                <!-- TEMPORARILY COMMENTED - Will be auto-filled with "Pro" subscription
                <ion-item class="custom">
                  <ion-label position="stacked" class="!mb-2">subscription</ion-label>
                  <ion-input
                    v-model="tenantForm.subcription_id"
                    class="custom"
                    fill="solid"
                    placeholder="ID de suscripción"
                    :disabled="loading"
                  ></ion-input>
                </ion-item>
                -->
              </ion-list>

              <!-- Error Alert -->
              <ion-alert
                v-if="error"
                class="error-alert"
              >
                <div class="error-content">
                  <ion-icon :icon="alertCircleOutline" class="error-icon"></ion-icon>
                  <p>{{ error }}</p>
                </div>
              </ion-alert>

              <!-- Success Alert -->
              <ion-alert
                v-if="success"
                class="success-alert"
              >
                <div class="success-content">
                  <ion-icon :icon="checkmarkCircleOutline" class="success-icon"></ion-icon>
                  <p>{{ success }}</p>
                </div>
              </ion-alert>

              <!-- Submit Button -->
              <div class="button-container">
                <ion-button
                  class="next-button"
                  expand="block"
                  type="submit"
                  :disabled="loading || !tenantForm.name"
                  color="primary"
                >
                  <ion-spinner v-if="loading" slot="start"></ion-spinner>
                  <ion-icon v-else :icon="addOutline" slot="start"></ion-icon>
                  {{ loading ? 'Creando...' : 'Crear Organización' }}
                </ion-button>
                
              </div>
            </form>
          </ion-card-content>
        </ion-card>

        <!-- Skip Button (for testing - remove in production) -->

      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore.js';
import API from '@/utils/api/index.js';
import ImageUpload from '@/components/common/ImageUpload.vue';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonTextarea,
  IonSelect,
  IonSelectOption,
  IonButton,
  IonButtons,
  IonIcon,
  IonSpinner,
  IonAlert
} from '@ionic/vue';
import {
  businessOutline,
  informationCircleOutline,
  shieldCheckmarkOutline,
  addOutline,
  logOutOutline,
  alertCircleOutline,
  checkmarkCircleOutline,
  imageOutline
} from 'ionicons/icons';

const router = useRouter();
const authStore = useAuthStore();

// Form state
const tenantForm = ref({
  name: null,
  description: null,
  img: null,              // ✅ Add this
  subcription_id: null      // ✅ Add this
});

const loading = ref(false);
const error = ref(null);
const success = ref(null);
const imageUploadRef = ref(null);
const proSubscriptionId = ref(null); // Store the "Pro" subscription ID

// Check if in development mode
const isDevelopment = computed(() => {
  return import.meta.env.DEV;
});

/**
 * Fetch subscriptions and find the "Pro" subscription ID
 * TEMPORARY FIX: Auto-select "Pro" subscription
 */
const fetchProSubscription = async () => {
  try {
    console.log('🔍 Fetching subscriptions to find "Pro" plan...');
    const response = await API.get(API.SUBSCRIPTION);
    const subscriptions = Array.isArray(response) ? response : (response?.data || []);
    
    // Find the subscription with name "Pro"
    const proSubscription = subscriptions.find(sub => sub.name === 'Pro');
    
    if (proSubscription) {
      proSubscriptionId.value = proSubscription.id;
      console.log('✅ Found "Pro" subscription:', proSubscription.id);
    } else {
      console.warn('⚠️ "Pro" subscription not found, using fallback');
      proSubscriptionId.value = 'CO'; // Fallback to default
    }
  } catch (err) {
    console.error('❌ Error fetching subscriptions:', err);
    // Use fallback on error
    proSubscriptionId.value = 'CO';
  }
};

// Lifecycle hook to fetch Pro subscription on component mount
onMounted(() => {
  fetchProSubscription();
});

/**
 * Handle image upload
 */
const handleImageChange = (fileInfo) => {
  console.log('📸 Organization logo uploaded:', fileInfo);
  // The tenantForm.img is automatically updated via v-model
};

/**
 * Handle image upload error
 */
const handleImageError = (errorMessage) => {
  console.error('❌ Image upload error:', errorMessage);
  error.value = errorMessage;
};

/**
 * Handles tenant creation
 */
const handleCreateTenant = async () => {
  loading.value = true;
  error.value = null;
  success.value = null;

  try {
    console.log('🏢 Creando tenant...', tenantForm.value);

    // Get file info from ImageUpload component
    const fileInfo = imageUploadRef.value?.getFileInfo();
    
    // TEMPORARY FIX: Use "Pro" subscription ID instead of manual input
    const subscriptionIdToUse = proSubscriptionId.value || tenantForm.value.subcription_id || 'CO';
    
    // Prepare payload - use FormData if there's a file, otherwise JSON
    let payload;
    
    if (fileInfo?.file) {
      // Has file - use FormData for file upload
      console.log('📦 Using FormData for file upload');
      const formData = new FormData();
      formData.append('name', tenantForm.value.name);
      formData.append('description', tenantForm.value.description || '');
      formData.append('subscription_id', subscriptionIdToUse); // Use Pro subscription
      formData.append('img', fileInfo.file);
      payload = formData;
    } else {
      // No file - use regular JSON
      console.log('📄 Using JSON payload (no file)');
      payload = {
        name: tenantForm.value.name,
        description: tenantForm.value.description || '',
        subscription_id: subscriptionIdToUse, // Use Pro subscription
        img: null
      };
    }

    // Call API to create tenant
    const response = await API.post(API.TENANT, payload);

    console.log('✅ Tenant creado:', response);
    success.value = '¡Organización creada exitosamente!';

    // Wait a moment to show success message
    setTimeout(async () => {
      // Refresh token to get updated tenant_id
      await refreshUserData();
      
      // Redirect to home or tenant dashboard
      router.push('/home');
    }, 1500);

  } catch (err) {
    console.error('❌ Error creando tenant:', err);
    error.value = err.message || 'Error al crear la organización. Intenta nuevamente.';
  } finally {
    loading.value = false;
  }
};

/**
 * Refresh user data to get updated tenant_id
 * Refreshes the token to get the updated JWT with tenant_id
 */
const refreshUserData = async () => {
  try {
    console.log('🔄 Refrescando token para obtener tenant_id actualizado...');
    
    // Call refresh token endpoint - no body needed, reads from httpOnly cookie
    const response = await API.post(API.REFRESH_TOKEN, {});
    
    // The API returns an array, get first element
    const data = Array.isArray(response) ? response[0] : response;
    
    if (!data || !data.access) {
      throw new Error('No se recibió access token en la respuesta');
    }
    
    console.log('✅ Token refrescado exitosamente');
    
    // Update token in authStore (which also updates sessionStorage)
    authStore.refreshToken(data.access);
    
    console.log('✅ Usuario actualizado con nuevo tenant_id:', authStore.tenantId);
    
  } catch (err) {
    console.error('❌ Error refrescando token:', err);
    throw err;
  }
};

/**
 * Handle logout
 */
const handleLogout = () => {
  console.log('👋 Cerrando sesión desde tenant setup...');
  authStore.logout();
  router.push('/login');
};

/**
 * Skip setup (only for development/testing)
 */
const skipSetup = () => {
  console.warn('⚠️ Omitiendo configuración de tenant (solo desarrollo)');
  router.push('/home');
};
</script>

<style scoped>
.section-description {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 20px 0;
  line-height: 1.5;
  padding: 12px;
  background: #f8fafc;
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
}
.verification-page::part(scroll) {
  background: url('/verify.jpg') no-repeat center center / cover;
}

.transparent-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

.transparent-toolbar {
  --background: rgba(180, 83, 9, 0); /* amber-700 with 10% opacity */
  --color: white;
}

.setup-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

/* Welcome Section */
.welcome-section {
  text-align: center;
  margin-bottom: 3rem;
}

.icon-wrapper {
  width: 120px;
  height: 120px;
  margin: 0 auto 2rem;
  background: linear-gradient(135deg, var(--ion-color-success) 0%, var(--ion-color-success-shade) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(132, 204, 22, 0.3);
}

.main-icon {
  font-size: 64px;
  color: white;
}

.welcome-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--ion-color-dark);
  margin-bottom: 1rem;
}

.welcome-subtitle {
  font-size: 1.1rem;
  color: var(--ion-color-medium);
  line-height: 1.6;
}

.welcome-subtitle strong {
  color: var(--ion-color-primary);
}

/* Info Cards */
.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.info-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-icon-wrapper {
  width: 48px;
  height: 48px;
  background: var(--ion-color-light);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.card-icon {
  font-size: 28px;
  color: var(--ion-color-primary);
}

.info-card h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 0.5rem;
}

.info-card p {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  line-height: 1.5;
}

/* Form Card */
.form-card {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-width: none;
  width: none;
}

/* Image Upload Section */
.image-upload-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.upload-label {
  display: block;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
}

/* Alerts */
.error-alert,
.success-alert {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 8px;
}

.error-alert {
  background: rgba(var(--ion-color-danger-rgb), 0.1);
  border-left: 4px solid var(--ion-color-danger);
}

.success-alert {
  background: rgba(var(--ion-color-success-rgb), 0.1);
  border-left: 4px solid var(--ion-color-success);
}

.error-content,
.success-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.error-icon {
  color: var(--ion-color-danger);
  font-size: 24px;
}

.success-icon {
  color: var(--ion-color-success);
  font-size: 24px;
}

.error-content p,
.success-content p {
  margin: 0;
  font-size: 0.9rem;
}

/* Button Container */
.button-container {
  margin-top: 2rem;
}

/* Skip Section */
.skip-section {
  text-align: center;
  margin-top: 2rem;
  padding: 1rem;
  background: var(--ion-color-warning-tint);
  border-radius: 8px;
  border: 1px dashed var(--ion-color-warning);
}

/* Responsive */
@media (max-width: 768px) {
  .setup-container {
    padding: 1rem 0.5rem;
  }

  .icon-wrapper {
    width: 100px;
    height: 100px;
  }

  .main-icon {
    font-size: 48px;
  }

  .welcome-title {
    font-size: 1.5rem;
  }

  .welcome-subtitle {
    font-size: 1rem;
  }

  .info-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .welcome-section {
  text-align: center;
  margin-bottom: 3rem;
  padding-inline: 10px;
}
}
</style>
