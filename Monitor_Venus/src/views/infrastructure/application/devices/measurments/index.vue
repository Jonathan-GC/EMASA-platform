<template>
  <ion-page>


    <ion-content :fullscreen="true">
      <div v-if="pageReady" class="current-dashboard">
        <!-- Main applications table with fetch data -->
        <TabsDeviceMeasurements
          :is-connected="isConnected"
          :reconnect-attempts="reconnectAttempts"
          :device="lastDevice"
          :chart-data-fragments="chartDataFragments"
          :latest-data-points="voltageLatestPoints"
          :chart-key="chartKey"
          :recent-messages="recentMessages"
          :current-chart-data-fragments="currentChartDataFragments"
          :current-latest-data-points="currentLatestPoints"
          :current-device="currentDevice"
          :current-chart-key="currentChartKey"
          :battery-chart-data-fragments="batteryChartDataFragments"
          :battery-latest-data-points="batteryLatestPoints"
          :battery-device="batteryDevice"
          :battery-chart-key="batteryChartKey"
          :get-battery-percentage="getBatteryPercentage"
          :measurement-devices="measurementDevices"
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
import { ref, onMounted, computed } from 'vue'
import { onIonViewWillEnter, onIonViewDidEnter } from '@ionic/vue'
import { useRoute } from 'vue-router'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import TableGateways from '@components/tables/gateways/TableGateways.vue'
import TabsDeviceMeasurements from '../../../../../components/tabs/tabsDeviceMeasurements.vue'
import { useWebSocket } from '@composables/useWebSocket.js'
import { useVoltageDataProcessor } from '@composables/useVoltageDataProcessor.js'
import { useCurrentDataProcessor } from '@composables/useCurrentDataProcessor.js'
import { useBatteryDataProcessor } from '@composables/useBatteryDataProcessor.js'
import { useMeasurementDataProcessor } from '@composables/useMeasurementDataProcessor.js'
import API from '@/utils/api/api.js'

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
  latestDataPoints: voltageLatestPoints,
  lastDevice, 
  recentMessages, 
  chartKey, 
  processIncomingData 
} = useVoltageDataProcessor()

// Use current data processor
const {
  chartDataFragments: currentChartDataFragments,
  latestDataPoints: currentLatestPoints,
  lastDevice: currentDevice,
  recentMessages: currentMessages,
  chartKey: currentChartKey,
  processIncomingData: processCurrentData
} = useCurrentDataProcessor()

// Use battery data processor
const {
  chartDataFragments: batteryChartDataFragments,
  latestDataPoints: batteryLatestPoints,
  lastDevice: batteryDevice,
  recentMessages: batteryMessages,
  chartKey: batteryChartKey,
  getBatteryPercentage,
  processIncomingData: processBatteryData
} = useBatteryDataProcessor()

// Map of active measurement processors
const measurementProcessors = new Map()

// Register default processors
measurementProcessors.set('voltage', { processor: { processIncomingData }, device: lastDevice })
measurementProcessors.set('current', { processor: { processIncomingData: processCurrentData }, device: currentDevice })
measurementProcessors.set('battery', { processor: { processIncomingData: processBatteryData }, device: batteryDevice })

// Function to create and register custom measurement processor
const registerMeasurementProcessor = (measurementType, config = {}) => {
  if (measurementProcessors.has(measurementType)) {
    console.log(`⚠️ Processor for ${measurementType} already exists, skipping registration`)
    return measurementProcessors.get(measurementType)
  }

  const processor = useMeasurementDataProcessor({
    measurementType,
    chartLabel: config.chartLabel || measurementType.charAt(0).toUpperCase() + measurementType.slice(1),
    unit: config.unit || '',
    chartColors: config.chartColors,
    specialProcessing: config.specialProcessing
  })

  measurementProcessors.set(measurementType, {
    processor,
    device: processor.lastDevice
  })

  console.log(`✅ Registered processor for ${measurementType}`)
  return measurementProcessors.get(measurementType)
}

// Combined message handler for all data types
const handleWebSocketMessage = (data) => {
  // Process data for all registered measurement types
  measurementProcessors.forEach((entry, measurementType) => {
    entry.processor.processIncomingData(data)
  })

  // Note: The data will be processed by all processors, but each will only
  // create chart data if the payload contains measurements for that type
}

// Computed property to create measurementDevices map for child component
const measurementDevices = computed(() => {
  const devices = {}
  
  // Add all processors' devices to the map
  measurementProcessors.forEach((entry, measurementType) => {
    devices[measurementType] = entry.device.value
  })
  
  return devices
})

// State for page readiness
const pageReady = ref(false)

/**
 * Preload last measurements from API to populate charts immediately
 */
const preloadLastMeasurements = async () => {
  try {
    console.log('📥 Preloading last measurements for device:', deviceId)
    // Fetch last 10 measurements as requested
    const response = await API.get(`${API.DEVICE_LAST_MEASUREMENT(deviceId)}?limit=10`)
    
    if (response) {
      console.log('✅ Preload data received:', response)
      // Process the preloaded data through all registered processors
      // We pass true for isPreload to avoid streaming animations for historical data
      measurementProcessors.forEach((entry) => {
        entry.processor.processIncomingData(response, true)
      })
    }
  } catch (error) {
    console.error('❌ Error preloading measurements:', error)
  }
}

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
  // Preload historical data before starting WebSocket
  preloadLastMeasurements()
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
