<template>
  <ion-page>
    <ion-header class="ion-no-border transparent-header">
      <ion-toolbar class="transparent-toolbar">
        <ion-buttons slot="start">
          <ion-back-button default-href="/home" class="text-neutral-50"></ion-back-button>
        </ion-buttons>
        <ion-title class="text-neutral-50 back-button-text">Regresar</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="verification-page">
      <!-- Header with Monitor Logo -->
      <div class="header-container">
        <img src="@/assets/monitor_logo_dark.svg" alt="Monitor Logo" class="logo" />
      </div>

      <!-- Centered Success Card -->
      <div class="verification-card-container">
        <ion-card class="verification-card">
          <ion-card-content class="card-content">
            <!-- Animated Success/Error Icon -->
            <div class="success-icon-container">
              <!-- Success Checkmark -->
              <div v-if="isVerified && !errorMessage" class="animated-checkmark">
                <svg class="checkmark-svg" viewBox="0 0 52 52">
                  <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                  <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
              </div>

              <!-- Error X Mark -->
              <div v-else-if="errorMessage && !isLoading" class="animated-error">
                <svg class="error-svg" viewBox="0 0 52 52">
                  <circle class="error-circle" cx="26" cy="26" r="25" fill="none"/>
                  <path class="error-x" fill="none" d="M16 16 36 36 M36 16 16 36"/>
                </svg>
              </div>

              <!-- Loading Spinner -->
              <ion-spinner v-else-if="isLoading" name="crescent" color="primary" class="loading-spinner"></ion-spinner>
            </div>

            <!-- Title -->
            <h1 class="verification-title">{{ errorMessage ? 'Verification Failed' : 'Email Verified!' }}</h1>

            <!-- Message -->
            <p v-if="!errorMessage" class="verification-message">
              Your email has been successfully verified. You can now access all features of the platform.
            </p>

            <!-- Error Message -->
            <p v-if="errorMessage" class="error-message">
              {{ errorMessage }}
            </p>

            <!-- Continue Button -->
            <ion-button 
              expand="block" 
              color="primary" 
              @click="goToLogin" 
              :disabled="isLoading || !isVerified"
              class="continue-button"
            >
              <ion-spinner v-if="isLoading" slot="start" name="crescent"></ion-spinner>
              <ion-icon v-else :icon="icons.arrowForward" slot="end"></ion-icon>
              {{ isLoading ? 'Verifying Account...' : 'Continue to Login' }}
            </ion-button>
          </ion-card-content>
        </ion-card>
      </div>

      <!-- Footer -->
      <AuthFooter />
    </ion-content>
  </ion-page>
</template>

<script setup>
import { inject, ref, onMounted } from 'vue'
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
const isLoading = ref(false)
const isVerified = ref(false)
const errorMessage = ref('')

// Verify account with token
const verifyAccount = async () => {
  if (!token.value) {
    console.error('No token found in URL')
    errorMessage.value = 'Invalid verification link'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await API.post(API.VERIFY_ACCOUNT, {
      token: token.value
    })

    console.log('Verification response:', response)
    isVerified.value = true
  } catch (error) {
    console.error('Verification error:', error)
    errorMessage.value = error.message || 'Failed to verify account'
    isVerified.value = false
  } finally {
    isLoading.value = false
  }
}

// Navigate to login
const goToLogin = () => {
  router.push(paths.LOGIN)
}

// Get token from URL and verify on mount
onMounted(async () => {
  token.value = route.query.token || ''
  console.log('Verification token:', token.value)
  
  // Fetch CSRF token first (required by backend)
  try {
    console.log('🔐 Fetching CSRF token...')
    await API.get(API.CSRF_TOKEN)
    console.log('✅ CSRF token obtained')
  } catch (error) {
    console.error('❌ Failed to fetch CSRF token:', error)
    errorMessage.value = 'Failed to initialize security token. Please try again.'
    isLoading.value = false
    return
  }
  
  // Automatically verify the account
  await verifyAccount()
})
</script>

<style scoped>
.verification-page {
  position: relative;
}

.verification-page::part(scroll) {
  background: url('/verify.jpg') no-repeat center center / cover;
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
  --background: rgba(180, 83, 9, 0.1); /* amber-700 with 10% opacity */
  --color: white;
}

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 3rem 1rem 2rem;
  position: relative;
  z-index: 2;
}


.logo {
  height: 60px;
  width: auto;
}

.verification-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 220px);
  z-index: 999999!important;
}

.verification-card {
  max-width: 500px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  z-index: 999999!important;
}

.card-content {
  text-align: center;
  padding: 3rem 2rem;
}

.success-icon-container {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Animated Checkmark Styles */
.animated-checkmark {
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.checkmark-svg {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
  stroke-width: 2;
  stroke: var(--ion-color-success);
  stroke-miterlimit: 10;
  box-shadow: inset 0px 0px 0px var(--ion-color);
}

.checkmark-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: var(--ion-color-success);
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark-check {
  transform-origin: 50% 50%;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  stroke: var(--ion-color-success);
  stroke-width: 3;
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
}

/* Keyframe Animations */
@keyframes stroke {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes scale {
  0%, 100% {
    transform: none;
  }
  50% {
    transform: scale3d(1.1, 1.1, 1);
  }
}

@keyframes fill {
  100% {
    box-shadow: inset 0px 0px 0px 30px var(--ion-color-success);
  }
}

/* Animated Error X Styles */
.animated-error {
  width: 80px;
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.error-svg {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
  stroke-width: 2;
  stroke: var(--ion-color-danger);
  stroke-miterlimit: 10;
}

.error-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: var(--ion-color-danger);
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.error-x {
  stroke-dasharray: 57;
  stroke-dashoffset: 57;
  stroke: var(--ion-color-danger);
  stroke-width: 3;
  stroke-linecap: round;
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
}

/* Loading Spinner */
.loading-spinner {
  width: 80px;
  height: 80px;
  font-size: 80px;
}

.verification-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-zinc-900);
  margin: 0 0 1rem;
}

.verification-message {
  font-size: 1rem;
  color: var(--color-zinc-600);
  line-height: 1.6;
  margin: 0 0 2rem;
}

.error-message {
  font-size: 0.95rem;
  color: var(--ion-color-danger);
  background-color: rgba(239, 68, 68, 0.1);
  padding: 0.75rem;
  border-radius: 8px;
  margin: 1rem 0;
  border-left: 3px solid var(--ion-color-danger);
}

.continue-button {
  margin-top: 1rem;
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

  .card-content {
    padding: 2rem 1.5rem;
  }

  .animated-checkmark,
  .animated-error,
  .loading-spinner {
    width: 64px;
    height: 64px;
    font-size: 64px;
  }

  .verification-title {
    font-size: 1.5rem;
  }

  .verification-message {
    font-size: 0.95rem;
  }
}
</style>
