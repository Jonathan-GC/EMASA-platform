<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-title>Proof of Concept</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content :fullscreen="true">
      <ion-header collapse="condense">
        <ion-toolbar>
          <ion-title size="large">Home</ion-title>
        </ion-toolbar>
      </ion-header>
      
      <div class="container">
        <div class="header-section">
          <ion-icon :icon="phonePortraitOutline" size="large" color="primary"></ion-icon>
          <h1>Vue + Vite + Capacitor</h1>
          <p>Cross-platform app running on Web, Android & iOS</p>
        </div>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Platform Information</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-item lines="none">
              <ion-label>
                <h3>Platform: {{ platformInfo.platform }}</h3>
                <p>Is Mobile: {{ platformInfo.isMobile ? 'Yes' : 'No' }}</p>
                <p>Is Desktop: {{ platformInfo.isDesktop ? 'Yes' : 'No' }}</p>
              </ion-label>
            </ion-item>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Device Features</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-button @click="showAlert" expand="block" fill="outline">
              <ion-icon :icon="alertCircleOutline" slot="start"></ion-icon>
              Show Alert
            </ion-button>
            
            <ion-button @click="showToast" expand="block" fill="outline">
              <ion-icon :icon="checkmarkCircleOutline" slot="start"></ion-icon>
              Show Toast
            </ion-button>
            
            <ion-button @click="vibrate" expand="block" fill="outline" :disabled="!canVibrate">
              <ion-icon :icon="phonePortraitOutline" slot="start"></ion-icon>
              Vibrate Device
            </ion-button>
            
            <ion-button @click="sendNotification" expand="block" fill="outline">
              <ion-icon :icon="notificationsOutline" slot="start"></ion-icon>
              Send Notification
            </ion-button>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Data Visualization</ion-card-title>
            <ion-card-subtitle>Chart.js Integration Demo</ion-card-subtitle>
          </ion-card-header>
          <ion-card-content>
            <div class="chart-tabs">
              <ion-segment v-model="selectedChart" @ionChange="handleChartChange">
                <ion-segment-button value="line">
                  <ion-label>Line</ion-label>
                </ion-segment-button>
                <ion-segment-button value="bar">
                  <ion-label>Bar</ion-label>
                </ion-segment-button>
                <ion-segment-button value="doughnut">
                  <ion-label>Doughnut</ion-label>
                </ion-segment-button>
              </ion-segment>
            </div>
            
            <ChartComponent 
              :key="selectedChart" 
              :type="selectedChart" 
              :title="getChartTitle(selectedChart)"
            />
            
            <ion-note class="chart-note">
              📊 Charts work seamlessly across web, Android, and iOS platforms
            </ion-note>
          </ion-card-content>
        </ion-card>

        <ion-card>
          <ion-card-header>
            <ion-card-title>Navigation</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-button @click="goToAbout" expand="block" fill="outline">
              <ion-icon :icon="informationCircleOutline" slot="start"></ion-icon>
              Go to About Page
            </ion-button>
            
            <ion-button @click="goToIotMonitor" expand="block" color="primary">
              <ion-icon :icon="barChartOutline" slot="start"></ion-icon>
              IoT Voltage Monitor
            </ion-button>
          </ion-card-content>
        </ion-card>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
//import ChartComponent from './ChartComponent.vue'

import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonCard, 
  IonCardHeader, 
  IonCardTitle, 
  IonCardSubtitle,
  IonCardContent, 
  IonButton, 
  IonIcon, 
  IonItem, 
  IonLabel,
  IonSegment,
  IonSegmentButton,
  IonNote,
  alertController,
  toastController,
  isPlatform
} from '@ionic/vue'
import { 
  phonePortraitOutline, 
  alertCircleOutline, 
  checkmarkCircleOutline, 
  informationCircleOutline,
  notificationsOutline,
  barChartOutline
} from 'ionicons/icons'
import { Capacitor } from '@capacitor/core'
import { Haptics, ImpactStyle } from '@capacitor/haptics'
import { LocalNotifications } from '@capacitor/local-notifications'

const router = useRouter()

const platformInfo = ref({
  platform: 'unknown',
  isMobile: false,
  isDesktop: false
})

const canVibrate = ref(false)
const selectedChart = ref('line')

onMounted(() => {
  // Get platform information
  platformInfo.value = {
    platform: Capacitor.getPlatform(),
    isMobile: isPlatform('mobile'),
    isDesktop: isPlatform('desktop')
  }
  
  // Check if device can vibrate
  canVibrate.value = Capacitor.isNativePlatform()
})

const showAlert = async () => {
  const alert = await alertController.create({
    header: 'Cross-Platform Alert',
    subHeader: 'Ionic + Capacitor',
    message: 'This alert works on web, Android, and iOS!',
    buttons: ['OK']
  })
  
  await alert.present()
}

const showToast = async () => {
  const toast = await toastController.create({
    message: 'Toast notification works across all platforms!',
    duration: 2000,
    position: 'bottom',
    color: 'success'
  })
  
  await toast.present()
}

const vibrate = async () => {
  try {
    await Haptics.impact({ style: ImpactStyle.Medium })
  } catch (error) {
    console.log('Vibration not available:', error)
  }
}

const sendNotification = async () => {
  try {
    // Request permission first
    const permission = await LocalNotifications.requestPermissions()
    
    if (permission.display === 'granted') {
      // Schedule a notification
      await LocalNotifications.schedule({
        notifications: [{
          title: 'Vue + Capacitor App',
          body: 'This is a native notification from your cross-platform app! 🚀',
          id: Math.floor(Math.random() * 1000000),
          schedule: { at: new Date(Date.now() + 1000) }, // 1 second from now
          sound: undefined,
          attachments: undefined,
          actionTypeId: '',
          extra: null
        }]
      })
      
      // Show a toast to confirm
      const toast = await toastController.create({
        message: 'Notification scheduled! Check your notification panel.',
        duration: 3000,
        position: 'bottom',
        color: 'success'
      })
      await toast.present()
    } else {
      // Permission denied
      const toast = await toastController.create({
        message: 'Notification permission denied. Please enable in settings.',
        duration: 3000,
        position: 'bottom',
        color: 'warning'
      })
      await toast.present()
    }
  } catch (error) {
    console.log('Notification error:', error)
    
    // Fallback for web or if notifications aren't available
    const toast = await toastController.create({
      message: 'Native notifications not available on this platform.',
      duration: 3000,
      position: 'bottom',
      color: 'medium'
    })
    await toast.present()
  }
}

const handleChartChange = (event) => {
  selectedChart.value = event.detail.value
}

const getChartTitle = (chartType) => {
  const titles = {
    line: 'User Growth & App Downloads (2024)',
    bar: 'Cross-Platform Usage Analytics',
    doughnut: 'Feature Usage Distribution'
  }
  return titles[chartType] || 'Chart'
}

const goToAbout = () => {
  router.push('/about')
}

const goToIotMonitor = () => {
  router.push('/voltage')
}
</script>

<style scoped>
.container {
  padding: 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h1 {
  margin: 20px 0 10px 0;
  color: var(--ion-color-primary);
}

.header-section p {
  color: var(--ion-color-medium);
  font-size: 16px;
}

ion-button {
  margin: 8px 0;
}

ion-card {
  margin-bottom: 20px;
}

.chart-tabs {
  margin-bottom: 15px;
}

.chart-note {
  display: block;
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
}
</style>
