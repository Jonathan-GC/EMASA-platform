<template>
  <ion-card v-if="needsTenantSetup" class="tenant-warning-card" color="warning">
    <ion-card-content>
      <div class="warning-content">
        <ion-icon :icon="warningOutline" class="warning-icon"></ion-icon>
        <div class="warning-text">
          <h3>Configuración Pendiente</h3>
          <p>Necesitas configurar tu organización para acceder a esta funcionalidad.</p>
          <ion-button 
            size="small" 
            color="dark" 
            @click="goToSetup"
          >
            Configurar Ahora
          </ion-button>
        </div>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth.js';
import {
  IonCard,
  IonCardContent,
  IonButton,
  IonIcon
} from '@ionic/vue';
import { warningOutline } from 'ionicons/icons';

const router = useRouter();
const { needsTenantSetup } = useAuth();

const goToSetup = () => {
  router.push('/tenant-setup');
};
</script>

