<template>
  <ion-page>
    <ion-content 
      :fullscreen="true" 
      class="h-full reset-password-page ion-no-padding" 
      :scroll-y="true"
      :keyboard-offset="!isMobile"
      scroll-events="false"
    >
      <ion-header class="ion-no-border transparent-header">
        <ion-toolbar color="amber-700/10 transparent-toolbar">
          <ion-buttons slot="start">
            <ion-back-button default-href="/home" class="text-neutral-50"></ion-back-button>
          </ion-buttons>
          <ion-title class="text-neutral-50">Regresar</ion-title>
        </ion-toolbar>
      </ion-header>

      <div class="login-background ">
        
        <div class="content-center min-h-full header-container">
          <img :src="MonitorLogo" alt="Monitor Logo" class="logo">
        </div>
        <div class="reset-card-container">
          <SignupForm/>
        </div>
        <AuthFooter />
        
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import MonitorLogo from '@assets/monitor_logo_dark.svg'
import { splineCurveMonotone } from "chart.js/helpers";
import { useResponsiveView } from '@composables/useResponsiveView.js'
import SignupForm from '../../../components/forms/auth/SignupForm.vue';

// Responsive view detection
const { isMobile } = useResponsiveView(768)

//import ComplexSignUp from '../../../components/forms/auth/ComplexSignUp.vue';
// El componente LoginForm se auto-importa gracias a unplugin-vue-components
</script>

<style scoped>
/*.container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}*/
.reset-password-page {
  position: relative;
}

.login-background {
  min-height: 100vh;
  background: url('/login.png') no-repeat center center / cover;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  width: auto;
}

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5rem 1rem 2rem;
}

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
.reset-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 1rem;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
}
</style>
