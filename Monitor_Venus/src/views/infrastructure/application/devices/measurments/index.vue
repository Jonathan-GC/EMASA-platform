<template>
  <ion-page>


    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="current-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <h1>📟 Devices </h1>
        </div>
        <!-- Main applications table with fetch data -->
        <TabsDeviceMeasurements
          :is-connected="isConnected"
          :reconnect-attempts="reconnectAttempts"
          :device="lastDevice"
          :chart-data-fragments="chartDataFragments"
          :chart-key="chartKey"
          :recent-messages="recentMessages"
          :current-chart-data="currentChartData"
          :current-device="currentDevice"
          :current-chart-key="currentChartKey"
          :battery-chart-data="batteryChartData"
          :battery-device="batteryDevice"
          :battery-chart-key="batteryChartKey"
          :battery-percentage="batteryPercentage"
        />
      </div>

      <!-- Loading state while page is preparing -->
      <div v-else class="page-loading">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Preparando página...</p>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue'
import { useRoute } from 'vue-router'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import TableGateways from '@components/tables/gateways/TableGateways.vue'
import TabsDeviceMeasurements from '../../../../../components/tabs/tabsDeviceMeasurements.vue'
import { useWebSocket } from '@composables/useWebSocket.js'
import { useVoltageDataProcessor } from '@composables/useVoltageDataProcessor.js'
import { useCurrentDataProcessor } from '@composables/useCurrentDataProcessor.js'
import { useBatteryDataProcessor } from '@composables/useBatteryDataProcessor.js'

// Get route params
const route = useRoute()
const deviceId = route.params.device_id
console.log('📍 Route params:', route.params)
console.log('🆔 Extracted deviceId:', deviceId)

// Use WebSocket composable with deviceId for API-based URL fetching
const { isConnected, reconnectAttempts, setOnMessage } = useWebSocket(deviceId)

// Use voltage data processor for chart data
const { 
  chartDataFragments, 
  lastDevice, 
  recentMessages, 
  chartKey, 
  processIncomingData 
} = useVoltageDataProcessor()

// Use current data processor
const {
  chartData: currentChartData,
  lastDevice: currentDevice,
  recentMessages: currentMessages,
  chartKey: currentChartKey,
  processIncomingData: processCurrentData
} = useCurrentDataProcessor()

// Use battery data processor
const {
  chartData: batteryChartData,
  lastDevice: batteryDevice,
  recentMessages: batteryMessages,
  chartKey: batteryChartKey,
  batteryPercentage,
  processIncomingData: processBatteryData
} = useBatteryDataProcessor()

// Combined message handler for all data types
const handleWebSocketMessage = (data) => {
  // Process data for all three measurement types
  processIncomingData(data)      // Voltage
  processCurrentData(data)       // Current
  processBatteryData(data)       // Battery
}

// State for page readiness
const pageReady = ref(false)

// Ionic lifecycle hooks
onIonViewWillEnter(() => {
  console.log('🚀 Gateway page will enter')
  pageReady.value = false
})

onIonViewDidEnter(() => {
  console.log('✅ Measurements page did enter')
  pageReady.value = true
})

onMounted(() => {
  console.log('🔧 Measurements page mounted')
  // Set up WebSocket message handler for all data types
  setOnMessage(handleWebSocketMessage)
})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.current-dashboard {
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  margin: 0 0 15px 0;
  color: #374151;
  font-size: 2rem;
  font-weight: 600;
}

.header-subtitle {
  display: flex;
  justify-content: center;
  align-items: center;
}

.no-data {
  margin: 40px 0;
  text-align: center;
}

.no-data ion-card {
  max-width: 500px;
  margin: 0 auto;
}

.no-data h2 {
  color: #6b7280;
  margin: 0 0 10px 0;
}

.no-data p {
  color: #9ca3af;
  margin: 8px 0;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .current-dashboard {
    padding: 15px;
  }

  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
