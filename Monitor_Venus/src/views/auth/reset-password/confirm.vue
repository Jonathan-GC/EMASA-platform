<template>
  <ion-page>
    <ion-content :fullscreen="true" class="reset-confirm-page">
      <ion-header class="ion-no-border transparent-header">
        <ion-toolbar class="transparent-toolbar">
          <ion-buttons slot="start">
            <ion-back-button default-href="/login" class="text-neutral-50"></ion-back-button>
          </ion-buttons>
          <ion-title class="text-neutral-50 back-button-text">Regresar</ion-title>
        </ion-toolbar>
      </ion-header>

      <div class="reset-confirm-background">
        <!-- Header with Monitor Logo -->
        <div class="header-container">
          <img src="@/assets/monitor_logo_dark.svg" alt="Monitor Logo" class="logo" />
        </div>

        <!-- Reset Password Confirm Card -->
        <div class="confirm-card-container">
          <ion-card class="confirm-card">
            <ion-card-content class="card-content">
              <!-- Title -->
              <h1 class="confirm-title">Establecer Nueva contraseña</h1>
              <p class="confirm-subtitle">
                Introduce tu nueva contraseña a continuación.
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
                <!-- New Password Input -->
                <ion-item lines="none" class="input-item">
                  <ion-icon :icon="icons.lock_closed" slot="start" class="input-icon"></ion-icon>
                  <ion-input
                    v-model="newPassword"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Nueva contraseña"
                    required
                    :disabled="isLoading"
                  ></ion-input>
                  <ion-button
                    slot="end"
                    fill="clear"
                    @click="showPassword = !showPassword"
                    class="toggle-password"
                  >
                    <ion-icon :icon="showPassword ? icons.eyeOff : icons.eye"></ion-icon>
                  </ion-button>
                </ion-item>

                <!-- Confirm Password Input -->
                <ion-item lines="none" class="input-item">
                  <ion-icon :icon="icons.lock_closed" slot="start" class="input-icon"></ion-icon>
                  <ion-input
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    placeholder="Confirma tu nueva contraseña"
                    required
                    :disabled="isLoading"
                  ></ion-input>
                  <ion-button
                    slot="end"
                    fill="clear"
                    @click="showConfirmPassword = !showConfirmPassword"
                    class="toggle-password"
                  >
                    <ion-icon :icon="showConfirmPassword ? icons.eyeOff : icons.eye"></ion-icon>
                  </ion-button>
                </ion-item>

                <!-- Password Requirements -->
                <div class="password-requirements">
                  <p class="requirements-title">La contraseña debe contener:</p>
                  <ul>
                    <li :class="{ valid: newPassword.length >= 8 }">
                      <ion-icon :icon="newPassword.length >= 8 ? icons.success : icons.ellipse"></ion-icon>
                      Al menos 8 caracteres
                    </li>
                    <li :class="{ valid: passwordsMatch && newPassword.length > 0 }">
                      <ion-icon :icon="passwordsMatch && newPassword.length > 0 ? icons.success : icons.ellipse"></ion-icon>
                      Las contraseñas coinciden
                    </li>
                  </ul>
                </div>

                <!-- Submit Button -->
                <ion-button
                  type="submit"
                  expand="block"
                  color="primary"
                  :disabled="isLoading || !isFormValid"
                  class="submit-button"
                >
                  <ion-spinner v-if="isLoading" slot="start" name="crescent"></ion-spinner>
                  <ion-icon v-else :icon="icons.checkmarkCircle" slot="start"></ion-icon>
                  {{ isLoading ? 'Resetting...' : 'Reset Password' }}
                </ion-button>
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
import { inject, ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
const route = useRoute()

// State
const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isLoading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

// Computed
const passwordsMatch = computed(() => {
  return newPassword.value === confirmPassword.value
})

const isFormValid = computed(() => {
  return (
    newPassword.value.length >= 8 &&
    passwordsMatch.value &&
    token.value
  )
})

// Handle form submission
const handleSubmit = async () => {
  if (!isFormValid.value) {
    errorMessage.value = 'Please ensure all requirements are met'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    // Fetch CSRF token first
    await API.get(API.CSRF_TOKEN)

    // Confirm password reset
    await API.post(API.RESET_PASSWORD_CONFIRM, {
      token: token.value,
      new_password: newPassword.value
    })

    successMessage.value = 'Password has been reset successfully! You can now login with your new password.'
  } catch (error) {
    console.error('Password reset confirm error:', error)
    errorMessage.value = error.message || 'Failed to reset password. The link may be invalid or expired.'
  } finally {
    isLoading.value = false
  }
}

// Navigate to login
const goToLogin = () => {
  router.push(paths.LOGIN)
}

// Get token from URL on mount
onMounted(() => {
  token.value = route.query.token || ''
  
  if (!token.value) {
    errorMessage.value = 'Invalid or missing reset token. Please request a new password reset link.'
  }
})
</script>

<style scoped>
.reset-confirm-page {
  position: relative;
}

.reset-confirm-background {
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

.confirm-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 1rem;
}

.confirm-card {
  max-width: 500px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
}

.card-content {
  padding: 2.5rem 2rem;
}

.confirm-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-zinc-900);
  margin: 0 0 0.5rem;
  text-align: center;
}

.confirm-subtitle {
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

.toggle-password {
  --padding-start: 0;
  --padding-end: 0;
  margin: 0;
}

.password-requirements {
  background-color: var(--ion-color-light);
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.requirements-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-zinc-700);
  margin: 0 0 0.5rem;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-requirements li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-zinc-600);
  margin-bottom: 0.5rem;
}

.password-requirements li:last-child {
  margin-bottom: 0;
}

.password-requirements li ion-icon {
  font-size: 1.25rem;
  color: var(--color-zinc-400);
}

.password-requirements li.valid {
  color: var(--ion-color-success);
}

.password-requirements li.valid ion-icon {
  color: var(--ion-color-success);
}

.submit-button {
  margin-top: 1.5rem;
  --border-radius: 8px;
  font-weight: 600;
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

  .confirm-title {
    font-size: 1.5rem;
  }

  .confirm-subtitle {
    font-size: 0.875rem;
  }
}
</style>
