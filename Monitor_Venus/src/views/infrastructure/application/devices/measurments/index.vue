<template>
  <ion-page>


    <ion-content :fullscreen="true" class="custom">
      <div v-if="pageReady && dataReady" class="current-dashboard">
        <!-- Main applications table with fetch data -->
        <TabsDeviceMeasurements
          :key="deviceId"
          :device-id="deviceId"
          :is-connected="isConnected"
          :reconnect-attempts="reconnectAttempts"
          :device="lastDevice"
          :measurements="measurements"
          :chart-data-fragments="chartDataFragments"
          :latest-data-points="voltageLatestPoints"
          :chart-key="chartKey"
          :recent-messages="recentMessages"
          :current-messages="currentMessages"
          :battery-messages="batteryMessages"
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
          :measurement-messages="measurementMessages"
          
          :power-chart-data-fragments="powerChartDataFragments"
          :power-latest-data-points="powerLatestDataPoints"
          :power-messages="powerMessages"
          
          :energy-chart-data-fragments="energyChartDataFragments"
          :energy-latest-data-points="energyLatestDataPoints"
          :energy-messages="energyMessages"
         
          :pressure-chart-data-fragments="pressureChartDataFragments"
          :pressure-latest-data-points="pressureLatestDataPoints"
          :pressure-messages="pressureMessages"
          
          :humidity-chart-data-fragments="humidityChartDataFragments"
          :humidity-latest-data-points="humidityLatestDataPoints"
          :humidity-messages="humidityMessages"
          
          :luminosity-chart-data-fragments="luminosityChartDataFragments"
          :luminosity-latest-data-points="luminosityLatestDataPoints"
          :luminosity-messages="luminosityMessages"
          
          :power-factor-chart-data-fragments="powerFactorChartDataFragments"
          :power-factor-latest-data-points="powerFactorLatestDataPoints"
          :power-factor-messages="powerFactorMessages"

          :real-power-chart-data-fragments="realPowerChartDataFragments"
          :real-power-latest-data-points="realPowerLatestDataPoints"
          :real-power-messages="realPowerMessages"

          :apparent-power-chart-data-fragments="apparentPowerChartDataFragments"
          :apparent-power-latest-data-points="apparentPowerLatestDataPoints"
          :apparent-power-messages="apparentPowerMessages"

          :reactive-power-chart-data-fragments="reactivePowerChartDataFragments"
          :reactive-power-latest-data-points="reactivePowerLatestDataPoints"
          :reactive-power-messages="reactivePowerMessages"

          :frequency-chart-data-fragments="frequencyChartDataFragments"
          :frequency-latest-data-points="frequencyLatestDataPoints"
          :frequency-messages="frequencyMessages"
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

// Use measurement data processors for new measurement types
const {
  chartDataFragments: powerChartDataFragments,
  latestDataPoints: powerLatestDataPoints,
  lastDevice: powerDevice,
  recentMessages: powerMessages,
  chartKey: powerChartKey,
  processIncomingData: processPowerData
} = useMeasurementDataProcessor({
  ref: 'power',
  label: 'Potencia',
  unit: 'W'
})

const {
  chartDataFragments: energyChartDataFragments,
  latestDataPoints: energyLatestDataPoints,
  lastDevice: energyDevice,
  recentMessages: energyMessages,
  chartKey: energyChartKey,
  processIncomingData: processEnergyData
} = useMeasurementDataProcessor({
  ref: 'energy',
  label: 'Energía',
  unit: 'kWh'
})

const {
  chartDataFragments: pressureChartDataFragments,
  latestDataPoints: pressureLatestDataPoints,
  lastDevice: pressureDevice,
  recentMessages: pressureMessages,
  chartKey: pressureChartKey,
  processIncomingData: processPressureData
} = useMeasurementDataProcessor({
  ref: 'pressure',
  label: 'Presión',
  unit: 'Psi'
})

const {
  chartDataFragments: humidityChartDataFragments,
  latestDataPoints: humidityLatestDataPoints,
  lastDevice: humidityDevice,
  recentMessages: humidityMessages,
  chartKey: humidityChartKey,
  processIncomingData: processHumidityData
} = useMeasurementDataProcessor({
  ref: 'humidity',
  label: 'Humedad',
  unit: '%'
})

const {
  chartDataFragments: luminosityChartDataFragments,
  latestDataPoints: luminosityLatestDataPoints,
  lastDevice: luminosityDevice,
  recentMessages: luminosityMessages,
  chartKey: luminosityChartKey,
  processIncomingData: processLuminosityData
} = useMeasurementDataProcessor({
  ref: 'luminosity',
  label: 'Luminosidad',
  unit: 'lx'
})

const {
  chartDataFragments: powerFactorChartDataFragments,
  latestDataPoints: powerFactorLatestDataPoints,
  lastDevice: powerFactorDevice,
  recentMessages: powerFactorMessages,
  chartKey: powerFactorChartKey,
  processIncomingData: processPowerFactorData
} = useMeasurementDataProcessor({
  ref: 'power_factor',
  label: 'Factor de Potencia',
  unit: ''
})

const {
  chartDataFragments: realPowerChartDataFragments,
  latestDataPoints: realPowerLatestDataPoints,
  lastDevice: realPowerDevice,
  recentMessages: realPowerMessages,
  chartKey: realPowerChartKey,
  processIncomingData: processRealPowerData
} = useMeasurementDataProcessor({
  ref: 'real_power',
  label: 'Potencia Real',
  unit: 'W'
})  

const {
  chartDataFragments: apparentPowerChartDataFragments,
  latestDataPoints: apparentPowerLatestDataPoints,
  lastDevice: apparentPowerDevice,
  recentMessages: apparentPowerMessages,
  chartKey: apparentPowerChartKey,
  processIncomingData: processApparentPowerData
} = useMeasurementDataProcessor({
  ref: 'apparent_power',
  label: 'Potencia Aparente',
  unit: 'VA'
})

const {
  chartDataFragments: reactivePowerChartDataFragments,
  latestDataPoints: reactivePowerLatestDataPoints,
  lastDevice: reactivePowerDevice,
  recentMessages: reactivePowerMessages,
  chartKey: reactivePowerChartKey,
  processIncomingData: processReactivePowerData
} = useMeasurementDataProcessor({
  ref: 'reactive_power',
  label: 'Potencia Reactiva',
  unit: 'VAr'
})

const {
  chartDataFragments: frequencyChartDataFragments,
  latestDataPoints: frequencyLatestDataPoints,
  lastDevice: frequencyDevice,
  recentMessages: frequencyMessages,
  chartKey: frequencyChartKey,
  processIncomingData: processFrequencyData
} = useMeasurementDataProcessor({
  ref: 'frequency',
  label: 'Frecuencia',
  unit: 'Hz'
})

// Map of active measurement processors
const measurementProcessors = new Map()

// Register default processors
measurementProcessors.set('voltage', { 
  processor: { processIncomingData, recentMessages }, 
  device: lastDevice 
})
measurementProcessors.set('current', { 
  processor: { processIncomingData: processCurrentData, recentMessages: currentMessages }, 
  device: currentDevice 
})
measurementProcessors.set('battery', { 
  processor: { processIncomingData: processBatteryData, recentMessages: batteryMessages }, 
  device: batteryDevice 
})

// Register new measurement processors
measurementProcessors.set('power', { 
  processor: { processIncomingData: processPowerData, recentMessages: powerMessages }, 
  device: powerDevice 
})
measurementProcessors.set('energy', { 
  processor: { processIncomingData: processEnergyData, recentMessages: energyMessages }, 
  device: energyDevice 
})
measurementProcessors.set('pressure', { 
  processor: { processIncomingData: processPressureData, recentMessages: pressureMessages }, 
  device: pressureDevice 
})
measurementProcessors.set('humidity', { 
  processor: { processIncomingData: processHumidityData, recentMessages: humidityMessages }, 
  device: humidityDevice 
})
measurementProcessors.set('luminosity', { 
  processor: { processIncomingData: processLuminosityData, recentMessages: luminosityMessages }, 
  device: luminosityDevice 
})
measurementProcessors.set('power_factor', { 
  processor: { processIncomingData: processPowerFactorData, recentMessages: powerFactorMessages }, 
  device: powerFactorDevice 
})
measurementProcessors.set('real_power', { 
  processor: { processIncomingData: processRealPowerData, recentMessages: realPowerMessages }, 
  device: realPowerDevice 
})
measurementProcessors.set('apparent_power', { 
  processor: { processIncomingData: processApparentPowerData, recentMessages: apparentPowerMessages }, 
  device: apparentPowerDevice 
})
measurementProcessors.set('reactive_power', { 
  processor: { processIncomingData: processReactivePowerData, recentMessages: reactivePowerMessages }, 
  device: reactivePowerDevice 
})
measurementProcessors.set('frequency', { 
  processor: { processIncomingData: processFrequencyData, recentMessages: frequencyMessages }, 
  device: frequencyDevice 
})

// Function to create and register custom measurement processor
const registerMeasurementProcessor = (measurementType, config = {}) => {
  // Avoid overwriting existing processors (e.g., defaults like voltage, current)
  if (measurementProcessors.has(measurementType)) {
    console.log(`⚠️ Processor for ${measurementType} already exists, skipping registration`)
    return measurementProcessors.get(measurementType)
  }

  // Fallback label: use provided label, otherwise a title‑cased version of the type
  const fallbackLabel = measurementType.charAt(0).toUpperCase() + measurementType.slice(1)
  const processor = useMeasurementDataProcessor({
    ref: measurementType,
    label: config.label || fallbackLabel,
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

// Computed property to create measurementMessages map for child component
const measurementMessages = computed(() => {
  const messages = {}
  
  // Add all processors' messages to the map
  measurementProcessors.forEach((entry, measurementType) => {
    messages[measurementType] = entry.processor.recentMessages.value
  })
  
  return messages
})

// State for page readiness
const pageReady = ref(false)
const dataReady = ref(false)
const measurements = ref([])

/**
 * Fetch measurements and register processors
 */
const fetchAndRegisterMeasurements = async () => {
  try {
    console.log('📊 Fetching measurements for device:', deviceId)
    const response = await API.get(API.DEVICE_GET_MEASUREMENTS(deviceId))
    measurements.value = Array.isArray(response) ? response : [response]
    
    measurements.value.forEach(m => {
      const type = m.ref?.toLowerCase()
      const excludedTypes = [
        'voltage', 
        'current', 
        'battery',
        'power',
        'energy',
        'pressure',
        'humidity',
        'luminosity',
        'power_factor',
        'real_power',
        'apparent_power',
        'reactive_power',
        'frequency',
      ]
      
      if (type && !excludedTypes.includes(type)) {
        registerMeasurementProcessor(type, {
          unit: m.unit,
          label: m.label,
          ref: m.ref,
          icon: m.icon
        })
      }
    })
  } catch (error) {
    console.error('❌ Error fetching measurements:', error)
  }
}

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

onMounted(async () => {
  console.log('🔧 Measurements page mounted')
  // Fetch measurements first to register all processors
  await fetchAndRegisterMeasurements()
  dataReady.value = true
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
