<template>
  <ion-page>
    <ion-content class="ion-padding">
      <div class="unauthorized-container">
        <div class="icon-wrapper">
          <ion-icon :icon="lockClosedOutline" class="lock-icon"></ion-icon>
        </div>
        
        <h1 class="title">Acceso Denegado</h1>
        
        <p class="message">
          No tienes permisos para acceder a esta página.
        </p>
        
        <div class="info-card">
          <ion-icon :icon="informationCircleOutline" class="info-icon"></ion-icon>
          <div class="info-text">
            <p class="info-title">¿Por qué veo esto?</p>
            <p class="info-description">
              Esta página requiere permisos de administrador o un rol específico 
              que tu cuenta no posee actualmente.
            </p>
          </div>
        </div>

        <div class="actions">
          <ion-button expand="block" @click="goToDashboard" color="primary">
            <ion-icon :icon="homeOutline" slot="start"></ion-icon>
            Ir al Dashboard
          </ion-button>
          
          <ion-button expand="block" fill="outline" @click="goBack">
            <ion-icon :icon="arrowBackOutline" slot="start"></ion-icon>
            Volver Atrás
          </ion-button>
        </div>

        <div class="user-info" v-if="authStore.isAuthenticated">
          <p class="user-label">Usuario actual:</p>
          <p class="user-name">{{ authStore.username }}</p>
          <ion-chip :color="getRoleColor()">
            <ion-label>{{ getRoleLabel() }}</ion-label>
          </ion-chip>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore.js';
import { 
  IonPage, 
  IonContent, 
  IonButton, 
  IonIcon,
  IonChip,
  IonLabel
} from '@ionic/vue';
import { 
  lockClosedOutline, 
  informationCircleOutline, 
  homeOutline,
  arrowBackOutline
} from 'ionicons/icons';

const router = useRouter();
const authStore = useAuthStore();

const goToDashboard = () => {
  router.push('/home');
};

const goBack = () => {
  router.back();
};

const getRoleLabel = () => {
  if (authStore.isSuperUser) return 'Super Usuario';
  if (authStore.isGlobalUser) return 'Usuario Global';
  if (authStore.isAdmin) return 'Administrador';
  return 'Usuario';
};

const getRoleColor = () => {
  if (authStore.isSuperUser) return 'danger';
  if (authStore.isAdmin) return 'warning';
  return 'primary';
};
</script>

<style scoped>
.unauthorized-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  text-align: center;
  padding: 2rem;
}

.icon-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.lock-icon {
  font-size: 64px;
  color: white;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--ion-color-dark);
  margin-bottom: 1rem;
}

.message {
  font-size: 1.1rem;
  color: var(--ion-color-medium);
  margin-bottom: 2rem;
  max-width: 500px;
}

.info-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: var(--ion-color-light);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  max-width: 500px;
  text-align: left;
}

.info-icon {
  font-size: 32px;
  color: var(--ion-color-primary);
  flex-shrink: 0;
}

.info-text {
  flex: 1;
}

.info-title {
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 0.5rem;
}

.info-description {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  line-height: 1.5;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  max-width: 400px;
  margin-bottom: 2rem;
}

.user-info {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--ion-color-light);
  border-radius: 12px;
  max-width: 400px;
}

.user-label {
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  margin-bottom: 0.25rem;
}

.user-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 0.5rem;
}

/* Responsive */
@media (max-width: 768px) {
  .icon-wrapper {
    width: 100px;
    height: 100px;
  }
  
  .lock-icon {
    font-size: 48px;
  }
  
  .title {
    font-size: 1.5rem;
  }
  
  .message {
    font-size: 1rem;
  }
}
</style>
