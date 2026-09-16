<template>
  <ion-page>
    <ion-content
      :fullscreen="true"
      class="h-full ion-no-padding"
      :scroll-y="isMobile"
    >
      <ion-header class="ion-no-border transparent-header">
        <ion-toolbar color="amber-700/10" class="transpatent-toolbar">
          <ion-buttons slot="start">
            <ion-back-button default-href="/login" class="text-neutral-50"></ion-back-button>
          </ion-buttons>
          <ion-title class="text-neutral-50 back-button-text">Regresar</ion-title>
        </ion-toolbar>
      </ion-header>

      <div class="login-background min-h-screen">
        <div class="content-center min-h-full header-container">
          <img :src="MonitorLogo" alt="Monitor Logo" class="logo">
        </div>
        <div class="reset-card-container">
          <OtpForm />
        </div>
        <AuthFooter />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import MonitorLogo from '@assets/monitor_logo_dark.svg'
import { useResponsiveView } from '@composables/useResponsiveView.js'

// Responsive view detection
const { isMobile } = useResponsiveView(768)

// El componente OtpForm se auto-importa gracias a unplugin-vue-components
</script>

<style scoped>
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

.reset-card-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  padding: 1rem;
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

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 5rem 1rem 2rem;
}

@media (max-width: 768px) {
  .back-button-text {
    display: none;
  }
}
</style>
