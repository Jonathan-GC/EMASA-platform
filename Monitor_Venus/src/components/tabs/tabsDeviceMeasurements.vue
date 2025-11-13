<template>
  <div class="tabs-device-measurements">
    <ion-tabs>
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="voltage">
          <ion-icon :icon="icons.flash"></ion-icon>
          <ion-label>Voltaje</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="current">
          <ion-icon :icon="icons.plug"></ion-icon>
          <ion-label>Corriente</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="battery">
          <ion-icon :icon="icons.batteryHalf"></ion-icon>
          <ion-label>Batería</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="activation">
          <ion-icon :icon="icons.key"></ion-icon>
          <ion-label>Activación</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="measurements">
          <ion-icon :icon="icons.analytics"></ion-icon>
          <ion-label>Mediciones</ion-label>
        </ion-tab-button>
      </ion-tab-bar>

      <!-- Voltage Tab -->
      <ion-tab tab="voltage">
        <ion-content class="ion-padding custom">
          <div class="tab-content">
            <!-- Header with connection status -->
            <div class="header flex">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>📟 Device Measurements - Voltage</h1>
              </div>
              <div class="header-subtitle connection-status">
                <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
              </div>

            </div>

            <!-- Device information section -->
            <DeviceInfo :device="device" />

            <!-- No data placeholder -->
            <div v-if="!device" class="no-data">
              <h2>🔍 Esperando datos del dispositivo...</h2>
              <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
              <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
            </div>

            <!-- Charts grid -->
            <ChartsGrid :chart-fragments="chartDataFragments" :chart-key="chartKey"
              :device-name="device?.device_name || deviceName" />

            <!-- Recent messages -->
            <RecentMessages :messages="recentMessages" />
          </div>
        </ion-content>
      </ion-tab>

      <!-- Current Tab -->
      <ion-tab tab="current">
        <ion-content class="ion-padding">
          <div class="tab-content">
            <!-- Header with connection status -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>📟 Device Measurements - Current</h1>
              </div>
              <div class="header-subtitle">
                <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
              </div>
            </div>

            <!-- Device information section -->
            <CurrentDeviceInfo :device="currentDevice" />

            <!-- No data placeholder -->
            <div v-if="!currentDevice" class="no-data">
              <h2>🔍 Esperando datos del dispositivo...</h2>
              <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
              <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
            </div>

            <!-- Current chart -->
            <div v-if="currentDevice" class="chart-container">
              <SingleCurrentChart :chart-data="currentChartData" :chart-key="currentChartKey"
                :device-name="currentDevice?.device_name || 'Dispositivo IoT'" />
            </div>

            <!-- Recent messages -->
            <RecentMessages :messages="recentMessages" />
          </div>
        </ion-content>
      </ion-tab>

      <!-- Battery Tab -->
      <ion-tab tab="battery">
        <ion-content class="ion-padding">
          <div class="tab-content">
            <!-- Header with connection status -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>📟 Device Measurements - Battery</h1>
              </div>
              <div class="header-subtitle">
                <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
              </div>
            </div>

            <!-- Device information section -->
            <BatteryDeviceInfo :device="batteryDevice" :battery-percentage="batteryPercentage" />

            <!-- No data placeholder -->
            <div v-if="!batteryDevice" class="no-data">
              <h2>🔍 Esperando datos del dispositivo...</h2>
              <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
              <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
            </div>

            <!-- Battery chart -->
            <div class="chart-container">
              <DualAxisBatteryChart :chart-data="batteryChartData" :chart-key="batteryChartKey"
                :device-name="batteryDevice?.device_name || 'Dispositivo IoT'" />
            </div>

            <!-- Recent messages -->
            <RecentMessages :messages="recentMessages" />
          </div>
        </ion-content>
      </ion-tab>

      <!-- Activation Tab -->
      <ion-tab tab="activation">
        <ion-content class="ion-padding">
          <div class="tab-content">
            <!-- Header -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>🔑 Device Activation</h1>
              </div>
              <div class="header-subtitle">
                Configure activation keys for your device
              </div>
            </div>

            <!-- Device information section -->
            <div v-if="device" class="device-info-section">
              <h3>Device: {{ device.device_name || device.name || 'Unknown Device' }}</h3>
              <p>EUI: {{ device.dev_eui || 'Not available' }}</p>
            </div>

            <!-- Activation form -->
            <div class="form-container">
              <FormActivationDevice type="device_activation" label="device activation" :device="device"
                @item-created="handleActivationCreated" @field-changed="handleActivationFieldChanged" />
            </div>

            <!-- Recent messages -->
            <RecentMessages :messages="recentMessages" />
          </div>
        </ion-content>
      </ion-tab>

      <!-- Measurements Tab -->
      <ion-tab tab="measurements">
        <ion-content class="ion-padding">
          <div class="tab-content">
            <!-- Header -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>📊 Device Measurements</h1>
              </div>
              <div class="header-subtitle">
                View measurement thresholds and limits
              </div>
            </div>

            <!-- Device information section -->
            <div v-if="device" class="device-info-section">
              <h3>Device: {{ device.device_name || device.name || 'Unknown Device' }}</h3>
              <p>EUI: {{ device.dev_eui || 'Not available' }}</p>
            </div>

            <!-- Loading state -->
            <div v-if="measurementsLoading" class="loading-container">
              <ion-spinner name="crescent" color="primary"></ion-spinner>
              <p>Loading measurements...</p>
            </div>

            <!-- Error state -->
            <div v-else-if="measurementsError" class="error-container">
              <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
              <p class="error-message">{{ measurementsError }}</p>
              <ion-button @click="fetchMeasurements" size="small">
                <ion-icon :icon="icons.refresh" slot="start"></ion-icon>
                Retry
              </ion-button>
            </div>

            <!-- Measurements Summary -->
            <div 
              v-else-if="measurements && measurements.length > 0" 
              class="measurements-container"
              :class="{ 'desktop-grid': isDesktop, 'mobile-stack': isMobile || isTablet }"
            >
              <!-- Loop through all measurements -->
              <ion-card 
                v-for="(measurement, index) in measurements" 
                :key="index" 
                class="measurement-card"
              >
                <ion-card-header>
                  <div class="card-header-content">
                    <div class="card-icon-wrapper">
                      <ion-icon :icon="icons.analytics" color="primary"></ion-icon>
                    </div>
                    <div class="card-title-section">
                      <ion-card-title>{{ measurement.unit || 'Measurement' }}</ion-card-title>
                      <ion-badge 
                        :color="getThresholdStatus(measurement)" 
                        class="status-badge"
                      >
                        {{ getThresholdStatusText(measurement) }}
                      </ion-badge>
                    </div>
                  </div>
                </ion-card-header>
                <ion-card-content>
                  <div class="measurements-grid">
                    <div class="measurement-item min">
                      <div class="measurement-icon">
                        <ion-icon :icon="icons.arrowDownCircle" color="success"></ion-icon>
                      </div>
                      <div class="measurement-info">
                        <span class="measurement-label">Mínimo</span>
                        <span class="measurement-value">{{ measurement.min }} <span class="unit-text">{{ measurement.unit }}</span></span>
                      </div>
                    </div>
                    
                    <div class="measurement-item max">
                      <div class="measurement-icon">
                        <ion-icon :icon="icons.arrowUpCircle" color="danger"></ion-icon>
                      </div>
                      <div class="measurement-info">
                        <span class="measurement-label">Máximo</span>
                        <span class="measurement-value">{{ measurement.max }} <span class="unit-text">{{ measurement.unit }}</span></span>
                      </div>
                    </div>
                    
                    <div class="measurement-item threshold">
                      <div class="measurement-icon">
                        <ion-icon :icon="icons.alert" color="warning"></ion-icon>
                      </div>
                      <div class="measurement-info">
                        <span class="measurement-label">Umbral</span>
                        <span class="measurement-value">{{ measurement.threshold }} <span class="unit-text">{{ measurement.unit }}</span></span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Range visualization -->
                  <div class="range-visualization">
                    <div class="range-bar">
                      <!-- Simple bar background -->
                      <div class="range-fill"></div>
                      <!-- Markers at key positions -->
                      <div class="range-marker" :style="{ left: '0%' }"></div>
                      <div class="range-marker" :style="{ left: calculateSafeZoneWidth(measurement) + '%' }"></div>
                      <div class="range-marker warning-marker" :style="{ left: (((measurement.max - measurement.threshold - measurement.min) / (measurement.max - measurement.min)) * 100) + '%' }"></div>
                      <div class="range-marker danger-marker" :style="{ left: '100%' }"></div>
                    </div>
                    <div class="range-labels">
                      <span class="range-label" :style="{ left: '0%' }">{{ formatValue(measurement.min) }}</span>
                      <span class="range-label" :style="{ left: calculateSafeZoneWidth(measurement) + '%' }">{{ formatValue(measurement.min + measurement.threshold) }}</span>
                      <span class="range-label" :style="{ left: (((measurement.max - measurement.threshold - measurement.min) / (measurement.max - measurement.min)) * 100) + '%' }">{{ formatValue(measurement.max - measurement.threshold) }}</span>
                      <span class="range-label" :style="{ left: '100%' }">{{ formatValue(measurement.max) }}</span>
                    </div>
                  </div>
                </ion-card-content>
              </ion-card>
            </div>

            <!-- No data state -->
            <div v-else class="no-data">
              <ion-icon :icon="icons.analytics" size="large" color="medium"></ion-icon>
              <h2>No measurement data available</h2>
              <p>Measurement data will appear here once available</p>
            </div>
          </div>

          <!-- Floating Action Buttons -->
          <FloatingActionButtons 
            entity-type="measurement"
            @refresh="fetchMeasurements"
            @itemCreated="handleMeasurementCreated"
          />
        </ion-content>
      </ion-tab>
    </ion-tabs>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonContent,
  IonIcon,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonSpinner,
  IonButton,
  IonBadge
} from '@ionic/vue'
import API from '@/utils/api/api.js'
import { useResponsiveView } from '@/composables/useResponsiveView.js'

// Chart.js imports and registration
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js'
import 'chartjs-adapter-date-fns'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

// Import device info components
import VoltageDeviceInfo from '@/components/cards/VoltageDeviceInfo.vue'
import CurrentDeviceInfo from '@/components/cards/CurrentDeviceInfo.vue'
import BatteryDeviceInfo from '@/components/cards/BatteryDeviceInfo.vue'
import RecentMessages from '@/components/cards/RecentMessages.vue'

// Import voltage view components
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import DeviceInfo from '@/components/cards/DeviceInfo.vue'
import ChartsGrid from '@/components/charts/ChartsGrid.vue'
import SingleCurrentChart from '@/components/charts/SingleCurrentChart.vue'
import DualAxisBatteryChart from '@/components/charts/DualAxisBatteryChart.vue'
import FormActivationDevice from '@/components/forms/create/device/formActivationDevice.vue'
import FloatingActionButtons from '@/components/operators/FloatingActionButtons.vue'

// Props
const props = defineProps({
  device: {
    type: Object,
    default: null
  },
  batteryPercentage: {
    type: Number,
    default: 0
  },
  recentMessages: {
    type: Array,
    default: () => []
  },
  // Additional props for voltage view layout
  isConnected: {
    type: Boolean,
    default: false
  },
  reconnectAttempts: {
    type: Number,
    default: 0
  },
  chartDataFragments: {
    type: Array,
    default: () => []
  },
  chartKey: {
    type: Number,
    default: 0
  },
  deviceName: {
    type: String,
    default: 'Dispositivo IoT'
  },
  // Current tab props
  currentChartData: {
    type: Object,
    default: () => ({ datasets: [] })
  },
  currentDevice: {
    type: Object,
    default: null
  },
  currentChartKey: {
    type: Number,
    default: 0
  },
  // Battery tab props
  batteryChartData: {
    type: Object,
    default: () => ({ datasets: [] })
  },
  batteryDevice: {
    type: Object,
    default: null
  },
  batteryChartKey: {
    type: Number,
    default: 0
  },
  batteryPercentage: {
    type: Number,
    default: 0
  }
})

// Inject icons
const icons = inject('icons', {})

// Router
const route = useRoute()

// Responsive view
const { isMobile, isTablet, isDesktop } = useResponsiveView()

// Component state
const isMounted = ref(false)
const measurements = ref(null)
const measurementsLoading = ref(false)
const measurementsError = ref(null)

// Fetch measurements from API
const fetchMeasurements = async () => {
  const deviceId = route.params.device_id
  
  if (!deviceId) {
    console.error('No device ID provided')
    measurementsError.value = 'Device ID is required'
    return
  }

  measurementsLoading.value = true
  measurementsError.value = null

  try {
    console.log('📊 Fetching measurements for device:', deviceId)
    const response = await API.get(API.DEVICE_GET_MEASUREMENTS(deviceId))
    
    // API returns array of measurements
    measurements.value = Array.isArray(response) ? response : [response]
    
    console.log('✅ Measurements fetched:', measurements.value)
  } catch (error) {
    console.error('❌ Error fetching measurements:', error)
    measurementsError.value = error.message || 'Failed to load measurements'
  } finally {
    measurementsLoading.value = false
  }
}

// Helper functions for status display
const getThresholdStatus = (data) => {
  if (!data) return 'medium'
  
  const range = data.max - data.min
  const position = data.threshold - data.min
  const percentage = (position / range) * 100
  
  if (percentage < 33) return 'success'
  if (percentage < 66) return 'warning'
  return 'danger'
}

const getThresholdStatusText = (data) => {
  if (!data) return 'Unknown'
  
  const status = getThresholdStatus(data)
  
  switch (status) {
    case 'success': return 'Bajo'
    case 'warning': return 'Medio'
    case 'danger': return 'Alto'
    default: return 'Unknown'
  }
}

const calculateThresholdPercentage = (data) => {
  if (!data || !data.min || !data.max || !data.threshold) return 0
  
  const range = data.max - data.min
  const position = data.threshold - data.min
  const percentage = (position / range) * 100
  
  return Math.max(0, Math.min(100, percentage))
}

const calculateSafeZoneWidth = (data) => {
  if (!data || !data.min || !data.max || !data.threshold) return 0
  
  const range = data.max - data.min
  const safeWidth = data.threshold // threshold is the buffer size
  
  return Math.max(0, Math.min(100, (safeWidth / range) * 100))
}

const calculateWarningValue = (data) => {
  if (!data || !data.min || !data.max || !data.threshold) return data?.min || 0
  
  // Warning zone ends at max - threshold
  return data.max - data.threshold
}

const calculateWarningZoneWidth = (data) => {
  if (!data || !data.min || !data.max || !data.threshold) return 0
  
  const range = data.max - data.min
  const warningStart = data.threshold
  const warningEnd = data.max - data.threshold
  const warningWidth = warningEnd - warningStart
  
  return Math.max(0, Math.min(100, (warningWidth / range) * 100))
}

const calculateDangerZoneWidth = (data) => {
  if (!data || !data.min || !data.max || !data.threshold) return 0
  
  const range = data.max - data.min
  const dangerStart = calculateWarningValue(data) - data.min
  const dangerWidth = data.max - calculateWarningValue(data)
  
  return Math.max(0, Math.min(100, (dangerWidth / range) * 100))
}

const formatValue = (value, unit) => {
  if (value === null || value === undefined) return 'N/A'
  
  // Format numbers nicely
  if (typeof value === 'number') {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k ${unit || ''}`
    } else if (value >= 100) {
      return `${value.toFixed(0)} ${unit || ''}`
    } else if (value >= 10) {
      return `${value.toFixed(1)} ${unit || ''}`
    } else {
      return `${value.toFixed(2)} ${unit || ''}`
    }
  }
  
  return `${value} ${unit || ''}`
}

onMounted(() => {
  isMounted.value = true
  fetchMeasurements()
})

// Watch for device ID changes and refetch
watch(() => route.params.deviceId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    fetchMeasurements()
  }
})

// Event handlers for activation form
function handleActivationCreated(itemName) {
  console.log('Device activation created:', itemName)
  // You can emit an event to parent component or show a success message
  // emit('activation-updated', itemName)
}

function handleActivationFieldChanged(fieldKey, value) {
  console.log('Activation field changed:', fieldKey, value)
  // Handle field changes if needed
}

// Event handler for measurement creation
function handleMeasurementCreated() {
  console.log('Measurement created, refreshing data...')
  fetchMeasurements()
}
</script>

<style scoped>
/* Measurements Tab Styles */
.measurements-container {
  max-width: 1400px;
  margin: 1.5rem auto;
  padding: 0 1rem;
}

.measurements-container.desktop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.measurements-container.mobile-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.measurement-card {
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  overflow: hidden;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  margin-bottom: 0;
}

.measurement-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.measurement-card ion-card-header {
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, rgba(var(--ion-color-primary-rgb), 0.05) 0%, rgba(var(--ion-color-primary-rgb), 0.02) 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.card-header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 56px;
  height: 56px;
  min-width: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(var(--ion-color-primary-rgb), 0.15) 0%, rgba(var(--ion-color-primary-rgb), 0.25) 100%);
  box-shadow: 0 4px 8px rgba(var(--ion-color-primary-rgb), 0.2);
}

.card-icon-wrapper ion-icon {
  font-size: 28px;
}

.card-title-section {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.measurement-card ion-card-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ion-color-dark);
  margin: 0;
}
.measurements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.measurement-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(var(--ion-color-light-rgb), 0.3);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.measurement-item:hover {
  background: rgba(var(--ion-color-light-rgb), 0.5);
  transform: translateX(4px);
}

.measurement-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 10px;
  background: white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.measurement-icon ion-icon {
  font-size: 22px;
}

.measurement-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.measurement-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ion-color-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.measurement-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ion-color-dark);
  line-height: 1.2;
}

.unit-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--ion-color-medium);
  margin-left: 0.25rem;
}

.range-visualization {
  margin-top: 1rem;
  padding-bottom: 1.5rem;
  padding-inline: 1rem;
}

.range-bar {
  position: relative;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  border: 1px solid #dee2e6;
}

.range-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 100%;
  background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
  border-radius: 4px;
  opacity: 0.3;
}

.range-marker {
  position: absolute;
  top: -4px;
  width: 2px;
  height: 16px;
  background: #495057;
  transform: translateX(-1px);
}

.warning-marker {
  background: #ffc107;
}

.danger-marker {
  background: #dc3545;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6c757d;
  position: relative;
  height: 24px;
}

.range-label {
  position: absolute;
  top: 8px;
  transform: translateX(-50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: #495057;
  white-space: nowrap;
}

/* Loading and error states */
.loading-container,
.error-container,
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
}

.loading-container ion-spinner {
  margin-bottom: 1rem;
}

.error-container ion-icon {
  margin-bottom: 1rem;
}

.error-message {
  color: var(--ion-color-danger);
  margin: 0.5rem 0 1rem;
}

.no-data ion-icon {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-data h2 {
  color: var(--ion-color-dark);
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.no-data p {
  color: var(--ion-color-medium);
  margin: 0;
}

.device-info-section {
  background-color: var(--ion-color-light);
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.device-info-section h3 {
  margin: 0 0 0.5rem;
  color: var(--ion-color-dark);
  font-size: 1.1rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .measurements-container {
    margin: 1rem auto;
    padding: 0 0.5rem;
  }

  .measurements-grid {
    grid-template-columns: 1fr;
  }

  .measurement-card ion-card-header {
    padding: 1rem;
  }

  .card-header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .card-title-section {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .measurement-card ion-card-title {
    font-size: 1.1rem;
  }

  .measurement-icon {
    width: 36px;
    height: 36px;
    min-width: 36px;
  }

  .measurement-icon ion-icon {
    font-size: 20px;
  }

  .measurement-value {
    font-size: 1.1rem;
  }

  .range-visualization {
    padding: 1rem;
  }

  .range-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .range-legend {
    flex-wrap: wrap;
  }

  .range-labels {
    font-size: 0.7rem;
  }

  .range-label-start,
  .range-label-warning,
  .range-label-threshold,
  .range-label-end {
    padding: 0.2rem 0.4rem;
    font-size: 0.7rem;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .measurements-container.desktop-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1400px) {
  .measurements-container.desktop-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

