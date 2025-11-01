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

<style scoped>
.tenant-warning-card {
  margin: 1rem 0;
  border-left: 4px solid var(--ion-color-warning-shade);
}

.warning-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.warning-icon {
  font-size: 32px;
  color: var(--ion-color-warning-contrast);
  flex-shrink: 0;
}

.warning-text {
  flex: 1;
}

.warning-text h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--ion-color-warning-contrast);
}

.warning-text p {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  color: var(--ion-color-warning-contrast);
}
</style>
