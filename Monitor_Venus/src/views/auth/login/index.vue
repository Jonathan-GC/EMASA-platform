<template>
  <ion-page>
    
    <ion-content :fullscreen="true" class="h-full">

      <ion-header collapse="condense">
        <ion-toolbar>
          <ion-title size="large">Login Test</ion-title>
        </ion-toolbar>
      </ion-header>


      <div class="login-background min-h-screen">
        <ion-header class="ion-no-border">
          <ion-toolbar color="amber-700/10">
            <ion-buttons slot="start">
              <ion-back-button default-href="/home" class="text-neutral-50"></ion-back-button>
            </ion-buttons>
            <ion-title class="text-neutral-50">Regresar</ion-title>
          </ion-toolbar>
        </ion-header>

        <div class="content-center min-h-full">
          <img :src="MonitorLogo" alt="Monitor Logo" class="logo">
          <LoginForm />
          <div class="text-center">
            <p><span class="text-amber-50">Al usar nuestros servicios, aceptas nuestros</span></p>
            <a>Terminos de Servicios y Política de privacidad</a>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import MonitorLogo from '@assets/monitor_logo_dark.svg'
import {splineCurveMonotone} from "chart.js/helpers";
// El componente LoginForm se auto-importa gracias a unplugin-vue-components
</script>

<style scoped>
/*.container {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}*/

.login-background {
  background-image: url("/login.png");
  background-size: cover;
  background-attachment: fixed;
}

.logo{
  display: block;
  margin: 0 auto;
  padding: 20px;
  max-width: 300px;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
}
</style>
