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
      </ion-tab-bar>

      <!-- Voltage Tab -->
      <ion-tab tab="voltage">
        <ion-content class="ion-padding">
          <div class="tab-content">
            <!-- Header with connection status -->
            <div class="header flex">
              <h1>📟 Device Measurements - Voltage</h1>
              <div class="header-subtitle connection-status">
                <ConnectionStatus
                  :is-connected="isConnected"
                  :reconnect-attempts="reconnectAttempts"
                />
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
            <ChartsGrid
              :chart-fragments="chartDataFragments"
              :chart-key="chartKey"
              :device-name="device?.device_name || deviceName"
            />

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
              <h1>📟 Device Measurements - Current</h1>
              <div class="header-subtitle">
                <ConnectionStatus
                  :is-connected="isConnected"
                  :reconnect-attempts="reconnectAttempts"
                />
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
              <SingleCurrentChart
                :chart-data="currentChartData"
                :chart-key="currentChartKey"
                :device-name="currentDevice?.device_name || 'Dispositivo IoT'"
              />
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
              <h1>📟 Device Measurements - Battery</h1>
              <div class="header-subtitle">
                <ConnectionStatus
                  :is-connected="isConnected"
                  :reconnect-attempts="reconnectAttempts"
                />
              </div>
            </div>

            <!-- Device information section -->
            <BatteryDeviceInfo
              :device="batteryDevice"
              :battery-percentage="batteryPercentage"
            />

            <!-- No data placeholder -->
            <div v-if="!batteryDevice" class="no-data">
              <h2>🔍 Esperando datos del dispositivo...</h2>
              <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
              <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
            </div>

            <!-- Battery chart -->
            <div class="chart-container">
              <DualAxisBatteryChart
                :chart-data="batteryChartData"
                :chart-key="batteryChartKey"
                :device-name="batteryDevice?.device_name || 'Dispositivo IoT'"
              />
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
              <h1>🔑 Device Activation</h1>
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
              <FormActivationDevice
                type="device_activation"
                label="device activation"
                :device="device"
                @item-created="handleActivationCreated"
                @field-changed="handleActivationFieldChanged"
              />
            </div>

            <!-- Recent messages -->
            <RecentMessages :messages="recentMessages" />
          </div>
        </ion-content>
      </ion-tab>
    </ion-tabs>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import {
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonContent,
  IonIcon,
  IonLabel
} from '@ionic/vue'

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

// Component state
const isMounted = ref(false)

onMounted(() => {
  isMounted.value = true
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
</script>

<style scoped>
.tabs-device-measurements {
  width: 100%;
}

.tab-content {
  padding: 16px 0;
}

/* Custom styling for tab content */
ion-content {
  --background: transparent;
}

/* Tab button styling */
ion-tab-button {
  --color-selected: #3b82f6;
  --color: #6b7280;
}

ion-tab-button.tab-selected {
  --color: #3b82f6;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .tab-content {
    padding: 8px 0;
  }

  ion-tab-button ion-label {
    display: none;
  }

  .header h1 {
    font-size: 1.5rem;
  }

  .no-data {
    margin: 20px 0;
  }
}

/* Voltage tab specific styles */
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

.chart-container {
  margin: 20px 0;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Activation tab specific styles */
.device-info-section {
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.device-info-section h3 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 1.2rem;
  font-weight: 600;
}

.device-info-section p {
  margin: 4px 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.form-container {
  margin: 20px 0;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>