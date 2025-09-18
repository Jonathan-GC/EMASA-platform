<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>About</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content :fullscreen="true">
      <ion-header collapse="condense">
        <ion-toolbar>
          <ion-title size="large">About</ion-title>
        </ion-toolbar>
      </ion-header>
      
      <div class="container">
        <div class="about-section">
          <ion-icon :icon="codeSlashOutline" size="large" color="secondary"></ion-icon>
          <h1>Cross-Platform Development</h1>
          <p>This app demonstrates the power of modern web technologies for cross-platform development.</p>
        </div>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Technology Stack</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-list>
              <ion-item>
                <ion-icon :icon="logoVue" slot="start" color="success"></ion-icon>
                <ion-label>
                  <h3>Vue 3</h3>
                  <p>Progressive JavaScript framework with Composition API</p>
                </ion-label>
              </ion-item>
              
              <ion-item>
                <ion-icon :icon="flashOutline" slot="start" color="warning"></ion-icon>
                <ion-label>
                  <h3>Vite</h3>
                  <p>Next generation frontend build tool for fast development</p>
                </ion-label>
              </ion-item>
              
              <ion-item>
                <ion-icon :icon="phonePortraitOutline" slot="start" color="primary"></ion-icon>
                <ion-label>
                  <h3>Capacitor</h3>
                  <p>Cross-platform native runtime for web apps</p>
                </ion-label>
              </ion-item>
              
              <ion-item>
                <ion-icon :icon="logoIonic" slot="start" color="primary"></ion-icon>
                <ion-label>
                  <h3>Ionic Framework</h3>
                  <p>UI components and tools for mobile and desktop</p>
                </ion-label>
              </ion-item>
              
              <ion-item>
                <ion-icon :icon="barChartOutline" slot="start" color="secondary"></ion-icon>
                <ion-label>
                  <h3>Chart.js</h3>
                  <p>Beautiful charts and data visualization across all platforms</p>
                </ion-label>
              </ion-item>
            </ion-list>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Platform Support</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-chip color="success">
              <ion-icon :icon="globeOutline"></ion-icon>
              <ion-label>Web</ion-label>
            </ion-chip>
            <ion-chip color="success">
              <ion-icon :icon="logoAndroid"></ion-icon>
              <ion-label>Android</ion-label>
            </ion-chip>
            <ion-chip color="success">
              <ion-icon :icon="logoApple"></ion-icon>
              <ion-label>iOS</ion-label>
            </ion-chip>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Features Demonstrated</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-list>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Platform detection</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Native alerts and toasts</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Device haptic feedback</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Native notifications</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Responsive design</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Navigation routing</ion-label>
              </ion-item>
              <ion-item>
                <ion-checkbox slot="start" :checked="true" disabled></ion-checkbox>
                <ion-label>Data visualization with Chart.js</ion-label>
              </ion-item>
            </ion-list>
          </ion-card-content>
        </ion-card>

        <div class="footer-section">
          <ion-button @click="goHome" expand="block" size="large">
            <ion-icon :icon="homeOutline" slot="start"></ion-icon>
            Back to Home
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonCard, 
  IonCardHeader, 
  IonCardTitle, 
  IonCardContent, 
  IonButton, 
  IonIcon, 
  IonList,
  IonItem, 
  IonLabel,
  IonChip,
  IonCheckbox,
  IonButtons,
  IonBackButton
} from '@ionic/vue'
import { 
  codeSlashOutline,
  logoVue,
  flashOutline,
  phonePortraitOutline,
  logoIonic,
  barChartOutline,
  globeOutline,
  logoAndroid,
  logoApple,
  homeOutline
} from 'ionicons/icons'

const router = useRouter()

const goHome = () => {
  router.push('/home')
}
</script>

<style scoped>
.container {
  padding: 20px;
}

.about-section {
  text-align: center;
  margin-bottom: 30px;
}

.about-section h1 {
  margin: 20px 0 10px 0;
  color: var(--ion-color-secondary);
}

.about-section p {
  color: var(--ion-color-medium);
  font-size: 16px;
  line-height: 1.5;
}

.footer-section {
  margin-top: 30px;
  text-align: center;
}

ion-card {
  margin-bottom: 20px;
}

ion-chip {
  margin: 4px;
}
</style>
