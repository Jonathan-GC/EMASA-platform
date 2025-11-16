<template>
  <ion-page>
    <ion-content :fullscreen="true" class="reset-password-page">
      <ion-header class="ion-no-border transparent-header">
        <ion-toolbar class="transparent-toolbar">
          <ion-buttons slot="start">
            <ion-back-button default-href="/login" class="text-neutral-50"></ion-back-button>
          </ion-buttons>
          <ion-title class="text-neutral-50 back-button-text">Regresar</ion-title>
        </ion-toolbar>
      </ion-header>

      <div class="reset-password-background">
        <!-- Header with Monitor Logo -->
        <div class="header-container">
          <img src="@/assets/monitor_logo_dark.svg" alt="Monitor Logo" class="logo" />
        </div>

        <!-- Reset Password Request Card -->
        <div class="reset-card-container">
          <ion-card class="reset-card">
            <ion-card-content class="card-content">
              <!-- Title -->
              <h1 class="reset-title">Restablecer Contraseña</h1>
              <p class="reset-subtitle">
                Introduce tu dirección de email y te enviaremos un enlace para restablecer tu contraseña.
              </p>

              <!-- Success Message -->
              <div v-if="successMessage" class="success-banner">
                <ion-icon :icon="icons.checkmarkCircle" class="success-icon"></ion-icon>
                <p>{{ successMessage }}</p>
              </div>

              <!-- Error Message -->
              <div v-if="errorMessage" class="error-banner">
                <ion-icon :icon="icons.alertCircle" class="error-icon"></ion-icon>
                <p>{{ errorMessage }}</p>
              </div>

              <!-- Form -->
              <form @submit.prevent="handleSubmit" v-if="!successMessage">
                <!-- Email Input -->
                <ion-item lines="none" class="input-item">
                  <ion-icon :icon="icons.mail" slot="start" class="input-icon"></ion-icon>
                  <ion-input
                    v-model="email"
                    type="email"
                    placeholder="Ingresa tu email"
                    required
                    :disabled="isLoading"
                  ></ion-input>
                </ion-item>

                <!-- Submit Button -->
                <ion-button
                  type="submit"
                  expand="block"
                  color="primary"
                  :disabled="isLoading || !email"
                  class="submit-button"
                >
                  <ion-spinner v-if="isLoading" slot="start" name="crescent"></ion-spinner>
                  <ion-icon v-else :icon="icons.send" slot="start"></ion-icon>
                  {{ isLoading ? 'Sending...' : 'Send Reset Link' }}
                </ion-button>

                <!-- Back to Login Link -->
                <div class="back-to-login">
                  <ion-button fill="clear" size="small" @click="goToLogin">
                    <ion-icon :icon="icons.arrowBack" slot="start"></ion-icon>
                    Back to Login
                  </ion-button>
                </div>
              </form>

              <!-- Success State - Show Login Button -->
              <div v-else>
                <ion-button
                  expand="block"
                  color="primary"
                  @click="goToLogin"
                  class="submit-button"
                >
                  <ion-icon :icon="icons.arrowForward" slot="end"></ion-icon>
                  Go to Login
                </ion-button>
              </div>
            </ion-card-content>
          </ion-card>
        </div>

        <!-- Footer -->
        <AuthFooter />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonButtons,
  IonBackButton,
  IonTitle,
  IonContent,
  IonCard,
  IonCardContent,
  IonItem,
  IonInput,
  IonButton,
  IonIcon,
  IonSpinner
} from '@ionic/vue'
import API from '@utils/api/api'
import AuthFooter from '@/components/layout/AuthFooter.vue'
import { paths } from '@/plugins/router/paths'

// Inject icons
const icons = inject('icons', {})

// Router
const router = useRouter()

// State
const email = ref('')
const isLoading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Handle form submission
const handleSubmit = async () => {
  if (!email.value) {
    errorMessage.value = 'Please enter your email address'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    // Fetch CSRF token first
    await API.get(API.CSRF_TOKEN)

    // Send password reset request
    await API.post(API.RESET_PASSWRORD_REQUEST, {
      email: email.value
    })

    successMessage.value = 'Password reset link has been sent to your email. Please check your inbox.'
  } catch (error) {
    console.error('Password reset request error:', error)
    errorMessage.value = error.message || 'Failed to send reset link. Please try again.'
  } finally {
    isLoading.value = false
  }
}

// Navigate to login
const goToLogin = () => {
  router.push(paths.LOGIN)
}
</script>

<style scoped>
.reset-password-page {
  position: relative;
}

.reset-password-background {
  min-height: 100vh;
  background: url('/electrics.jpg') no-repeat center center / cover;
  display: flex;
  flex-direction: column;
}

/* Transparent Header */
.transparent-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

.transparent-toolbar {
  --background: rgba(180, 83, 9, 0);
  --color: white;
}

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5rem 1rem 2rem;
}

.logo {
  height: 60px;
  width: auto;
}

.reset-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 1rem;
}

.reset-card {
  max-width: 500px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
}

.card-content {
  padding: 2.5rem 2rem;
}

.reset-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-zinc-900);
  margin: 0 0 0.5rem;
  text-align: center;
}

.reset-subtitle {
  font-size: 0.95rem;
  color: var(--color-zinc-600);
  text-align: center;
  margin: 0 0 2rem;
  line-height: 1.5;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: rgba(34, 197, 94, 0.1);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  border-left: 3px solid var(--ion-color-success);
}

.success-icon {
  color: var(--ion-color-success);
  font-size: 1.5rem;
  flex-shrink: 0;
}

.success-banner p {
  margin: 0;
  color: var(--ion-color-success);
  font-size: 0.95rem;
  line-height: 1.5;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: rgba(239, 68, 68, 0.1);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  border-left: 3px solid var(--ion-color-danger);
}

.error-icon {
  color: var(--ion-color-danger);
  font-size: 1.5rem;
  flex-shrink: 0;
}

.error-banner p {
  margin: 0;
  color: var(--ion-color-danger);
  font-size: 0.95rem;
  line-height: 1.5;
}

.input-item {
  --background: var(--ion-color-light);
  --border-radius: 8px;
  --padding-start: 12px;
  --padding-end: 12px;
  margin-bottom: 1rem;
  border: 1px solid var(--color-zinc-200);
}

.input-icon {
  color: var(--ion-color-medium);
  margin-right: 0.5rem;
}

.submit-button {
  margin-top: 1.5rem;
  --border-radius: 8px;
  font-weight: 600;
}

.back-to-login {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .back-button-text {
    display: none;
  }

  .logo {
    height: 48px;
  }

  .header-container {
    padding: 4rem 1rem 1.5rem;
  }

  .card-content {
    padding: 2rem 1.5rem;
  }

  .reset-title {
    font-size: 1.5rem;
  }

  .reset-subtitle {
    font-size: 0.875rem;
  }
}
</style>
