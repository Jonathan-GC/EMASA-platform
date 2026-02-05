<template>
  <div v-if="loaded" class="tabs-device-measurements">
    <ion-tabs>
      <ion-tab-bar slot="bottom">
        <!-- Dynamic measurement tabs -->
        <ion-tab-button 
          v-for="measurement in measurements" 
          :key="measurement.id"
          :tab="`measurement-${measurement.id}`"
        >
          <ion-icon :icon="icons[measurement.icon] || icons.analytics"></ion-icon>
          <ion-label>{{ capitalizeFirst(measurement.unit) }}</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="comparison">
          <ion-icon :icon="icons.git_compare"></ion-icon>
          <ion-label>Comparación</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="activation">
          <ion-icon :icon="icons.key"></ion-icon>
          <ion-label>Activación</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="measurements">
          <ion-icon :icon="icons.analytics"></ion-icon>
          <ion-label>Variables</ion-label>
        </ion-tab-button>
      </ion-tab-bar>

      <!-- Dynamic Measurement Tabs -->
      <ion-tab 
        v-for="measurement in measurements" 
        :key="measurement.id"
        :tab="`measurement-${measurement.id}`"
      >
        <ion-content class="ion-padding custom">
          <div class="tab-content">
            <!-- Header with connection status -->
            <div class="header flex">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>
                  <ion-icon :icon="icons[measurement.icon] || icons.analytics" size="large"></ion-icon>
                  {{ capitalizeFirst(measurement.unit) }}</h1>
              </div>
              <div class="header-subtitle connection-status">
                <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
              </div>
            </div>

            <!-- Device information section -->
            <MeasurementDeviceInfo :device="getMeasurementDevice(measurement)" :measurement="measurement" />

            <!-- Measurement configuration card -->
            <ion-card class="measurement-config-card">
              <ion-card-header>
                <div class="card-header-content">
                  <div class="card-title-section">
                    <ion-card-title>Configuración - {{ capitalizeFirst(measurement.unit) }}</ion-card-title>
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
                      <span class="measurement-value">{{ measurement.min }} <span class="unit-text">{{ measurement.ref }}</span></span>
                    </div>
                  </div>
                  
                  <div class="measurement-item max">
                    <div class="measurement-icon">
                      <ion-icon :icon="icons.arrowUpCircle" color="danger"></ion-icon>
                    </div>
                    <div class="measurement-info">
                      <span class="measurement-label">Máximo</span>
                      <span class="measurement-value">{{ measurement.max }} <span class="unit-text">{{ measurement.ref }}</span></span>
                    </div>
                  </div>
                  
                  <div class="measurement-item threshold">
                    <div class="measurement-icon">
                      <ion-icon :icon="icons.alert" color="warning"></ion-icon>
                    </div>
                    <div class="measurement-info">
                      <span class="measurement-label">Umbral</span>
                      <span class="measurement-value">{{ measurement.threshold }} <span class="unit-text">{{ measurement.ref }}</span></span>
                    </div>
                  </div>
                </div>
                
                <!-- Range visualization -->
                <div class="range-visualization">
                  <div class="range-bar">
                    <div class="range-fill"></div>
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

            <!-- Charts grid - dynamically select version based on measurement type -->
            <component 
              :is="getComponentForUnit(measurement.unit)"
              v-if="getMeasurementChartData(measurement.unit).length > 0"
              :chart-fragments="getMeasurementChartData(measurement.unit)" 
              :chart-key="chartKey"
              :latest-data-points="getMeasurementLatestDataPoints(measurement.unit)"
              :device-name="getMeasurementDevice(measurement)?.device_name || deviceName"
              :y-axis-min="measurement.min"
              :y-axis-max="measurement.max" 
              :threshold="measurement.threshold"
              :y-left-label="getProfileByValue(measurement.unit)?.label + ' (' + getProfileByValue(measurement.unit)?.unit + ')'"
              :y-right-label="getProfileByValue(measurement.unit)?.secondaryUnit ? getProfileByValue(measurement.unit).secondaryUnit : ''"
              :realtime-options="getProfileByValue(measurement.unit)?.realtime"
            />

            <!-- Placeholder when no chart data available -->
            <div v-else class="charts-section">
              <h3 class="section-title">📈 Real-time {{ capitalizeFirst(measurement.unit) }} Data</h3>
              <div class="waiting-data-card">
                <ion-icon :icon="icons.time" size="large" color="medium"></ion-icon>
                <p>Esperando datos en tiempo real de {{ measurement.unit }}...</p>
                <p class="hint-text">Los datos aparecerán aquí cuando el dispositivo envíe mediciones de {{ measurement.unit }}</p>
              </div>
            </div>

            <HistoricalMeasurementChart 
              v-if="deviceId || (device && device.id)"
              :device-id="deviceId || device.id"
              :available-measurements="measurements"
              :initial-type="measurement.unit?.toLowerCase()"
            />

            <!-- Recent messages -->
            <RecentMessages :messages="getMeasurementRecentMessages(measurement.unit)" :measurement-type="measurement.unit?.toLowerCase()" />

            <!-- Historical Measurement Chart -->
            
          </div>
        </ion-content>
      </ion-tab>

      <!-- Comparison Tab -->
      <ion-tab tab="comparison">
        <ion-content class="ion-padding custom">
          <div class="tab-content">
            <!-- Header -->
            <div class="header">
              <div class="header-title">
                <h1>
                  <ion-icon :icon="icons.git_compare" size="large"></ion-icon>
                   Comparación de Variables
                </h1>
              </div>
              <div class="header-subtitle connection-status">
                <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
              </div>
            </div>


            <!-- Measurement Selection Card -->
            <ion-card class="measurement-selector-card">
              <ion-card-header>
                <ion-card-title>
                  <ion-icon :icon="icons.target" size="small"></ion-icon>
                  Seleccionar Variables
                </ion-card-title>
                <ion-card-subtitle>Elige dos variables diferentes para comparar</ion-card-subtitle>
              </ion-card-header>
              <ion-card-content>
                <div class="selector-grid" :class="{ 'is-mobile': isMobile }">
                  <!-- Measurement 1 Selector -->
                  <div class="selector-item">
                    <label class="selector-label">Primera Variable</label>
                    <select v-model="selectedMeasurement1" class="measurement-select" @change="onMeasurementSelectionChange">
                      <option value="" disabled>Selecciona una variable</option>
                      <option 
                        v-for="measurement in getAvailableMeasurements()"
                        :key="'m1-' + measurement.id"
                        :value="measurement.unit.toLowerCase()"
                        :disabled="measurement.unit.toLowerCase() === selectedMeasurement2"
                      >
                        {{ capitalizeFirst(measurement.unit) }} ({{ measurement.ref || 'N/A' }})
                      </option>
                    </select>
                    
                    <!-- Channel selector for measurement 1 -->
                    <div class="channel-selector-inline">
                      <label class="channel-label">Canal</label>
                      <select v-model="selectedChannel1" class="channel-select-inline" @change="onMeasurementSelectionChange">
                        <option value="">Todos</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                      </select>
                    </div>
                  </div>

                  <!-- VS Divider -->
                  <div class="vs-divider" v-if="!isMobile">
                    <span>VS</span>
                  </div>

                  <!-- Measurement 2 Selector -->
                  <div class="selector-item">
                    <label class="selector-label">Segunda Variable</label>
                    <select v-model="selectedMeasurement2" class="measurement-select" @change="onMeasurementSelectionChange">
                      <option value="" disabled>Selecciona una variable</option>
                      <option 
                        v-for="measurement in getAvailableMeasurements()"
                        :key="'m2-' + measurement.id"
                        :value="measurement.unit.toLowerCase()"
                        :disabled="measurement.unit.toLowerCase() === selectedMeasurement1"
                      >
                        {{ capitalizeFirst(measurement.unit) }} ({{ measurement.ref || 'N/A' }})
                      </option>
                    </select>
                    
                    <!-- Channel selector for measurement 2 -->
                    <div class="channel-selector-inline">
                      <label class="channel-label">Canal</label>
                      <select v-model="selectedChannel2" class="channel-select-inline" @change="onMeasurementSelectionChange">
                        <option value="">Todos</option>
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                      </select>
                    </div>
                  </div>
                </div>

                <!-- Info message -->
                <div class="info-message" v-if="selectedMeasurement1 || selectedMeasurement2">
                  <ion-icon :icon="icons.info"></ion-icon>
                  <span>Selecciona dos variables diferentes para ver la comparación</span>
                </div>
              </ion-card-content>
            </ion-card>

            <!-- Combined Historical Chart -->
            <CombinedHistoricalChart 
              v-if="device && selectedMeasurement1 && selectedMeasurement2 && selectedMeasurement1 !== selectedMeasurement2"
              :key="`${selectedMeasurement1}-${selectedMeasurement2}-${selectedChannel1}-${selectedChannel2}`"
              :device-id="deviceId || device.id"
              :measurement1-type="selectedMeasurement1"
              :measurement2-type="selectedMeasurement2"
              :channel1="selectedChannel1"
              :channel2="selectedChannel2"
              :available-measurements="measurements"
              :initial-filters="comparisonFilters"
              @filters-changed="handleComparisonFiltersChange"
            />

            <!-- No measurements warning -->
            <ion-card v-else-if="!measurements || measurements.length < 2" class="warning-card">
              <ion-card-content>
                <div class="warning-content">
                  <ion-icon :icon="icons.warning" size="large"></ion-icon>
                  <p>Se necesitan al menos dos tipos de mediciones diferentes para comparar.</p>
                  <p v-if="!measurements || measurements.length === 0">No hay mediciones registradas para este dispositivo.</p>
                  <p v-else-if="measurements.length === 1">Solo hay una medición registrada. Registra más mediciones para usar esta función.</p>
                </div>
              </ion-card-content>
            </ion-card>
          </div>
        </ion-content>
      </ion-tab>

      <!-- Activation Tab -->
      <ion-tab tab="activation">
        <ion-content class="ion-padding custom">
          <div class="tab-content">
            <!-- Header -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>
                  <ion-icon :icon="icons.key" size="large"></ion-icon>
                  Activación del dispositivo
                </h1>
              </div>
            </div>

            <!-- Device information section -->
            <div v-if="device" class="device-info-section">
              <h3>Device: {{ device.device_name || device.name || 'Unknown Device' }}</h3>
              <p>EUI: {{ device.dev_eui || 'Not available' }}</p>
            </div>

            <!-- Activation form -->
            <div class="form-container">
              <!-- prefer the richer deviceDetails fetched from the API, fallback to device prop -->
              <!-- prefer the richer deviceDetails fetched from the API, fallback to device prop -->
              <!-- spread deviceDetails into a plain object to ensure child receives an object (not a ref) -->
              <FormActivationDevice type="device_activation" label="device activation" :device="deviceDetails ? { ...deviceDetails } : device"
                @item-created="handleActivationCreated" @field-changed="handleActivationFieldChanged" />
            </div>
          </div>
        </ion-content>
      </ion-tab>

      <!-- Measurements Tab -->
      <ion-tab tab="measurements">
        <ion-content class="ion-padding custom">
          <div class="tab-content">
            <!-- Header -->
            <div class="header">
              <div class="header-title">
                <ion-back-button default-href="/home"></ion-back-button>
                <h1>
                  <ion-icon :icon="icons.analytics" size="large"></ion-icon>
                  Variables del dispositivo
                </h1>
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
              <p>Cargando variables...</p>
            </div>

            <!-- Error state -->
            <ion-card v-else-if="measurementsError" class="error-card">
              <ion-card-content>
                <div class="error-container">
                  <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
                  <h2>Error al cargar variables</h2>
                  <p class="error-message">{{ measurementsError }}</p>
                  <ion-button @click="fetchMeasurements" shape="round" fill="outline" color="danger">
                    <ion-icon :icon="icons.refresh" slot="start"></ion-icon>
                    Reintentar
                  </ion-button>
                </div>
              </ion-card-content>
            </ion-card>

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
                      <ion-icon :icon="icons[measurement.icon]" color="primary"></ion-icon>
                    </div>
                    <div class="card-title-section">
                      <ion-card-title>{{ capitalizeFirst(measurement.unit) || 'Measurement' }}</ion-card-title>
                      <ion-badge 
                        :color="getThresholdStatus(measurement)" 
                        class="status-badge"
                      >
                        {{ getThresholdStatusText(measurement) }}
                      </ion-badge>
                      <quick-actions 
                        type="measurement"
                        to-edit
                        to-delete
                        :name="measurement.unit"
                        :index="measurement.id"
                        :initial-data="setMeasurementInitialData(measurement)"
                        @item-edited="handleMeasurementCreated"
                        @item-deleted="handleMeasurementCreated"
                      />
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
                        <span class="measurement-value">{{ measurement.min }} <span class="unit-text">{{ measurement.ref }}</span></span>
                      </div>
                    </div>
                    
                    <div class="measurement-item max">
                      <div class="measurement-icon">
                        <ion-icon :icon="icons.arrowUpCircle" color="danger"></ion-icon>
                      </div>
                      <div class="measurement-info">
                        <span class="measurement-label">Máximo</span>
                        <span class="measurement-value">{{ measurement.max }} <span class="unit-text">{{ measurement.ref }}</span></span>
                      </div>
                    </div>
                    
                    <div class="measurement-item threshold">
                      <div class="measurement-icon">
                        <ion-icon :icon="icons.alert" color="warning"></ion-icon>
                      </div>
                      <div class="measurement-info">
                        <span class="measurement-label">Umbral</span>
                        <span class="measurement-value">{{ measurement.threshold }} <span class="unit-text">{{ measurement.ref }}</span></span>
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
            <div v-else class="no-data-empty-state">
              <ion-icon :icon="icons.analytics" class="empty-icon"></ion-icon>
              <h2>Sin variables registradas</h2>
              <p>No se ha registrado Variables para este nodo</p>
              <ion-button fill="clear" @click="fetchMeasurements" color="medium">
                <ion-icon :icon="icons.refresh" slot="start"></ion-icon>
                Actualizar
              </ion-button>
            </div>
          </div>

          <!-- Floating Action Buttons -->
          <FloatingActionButtons 
            entity-type="measurement"
            @refresh="fetchMeasurements(true)"
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
import { capitalizeFirst} from '@utils/formatters/formatters.js'
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
import { MEASUREMENT_PROFILES, getProfileByValue } from '@/data/measurementProfiles.js'
import HistoricalMeasurementChart from '@/components/charts/HistoricalMeasurementChart.vue'
import CombinedHistoricalChart from '@/components/charts/CombinedHistoricalChart.vue'
import { format, subDays } from 'date-fns'

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
import MeasurementDeviceInfo from '@/components/cards/MeasurementDeviceInfo.vue'
import RecentMessages from '@/components/cards/RecentMessages.vue'

// Import voltage view components
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import DeviceInfo from '@/components/cards/DeviceInfo.vue'
import ChartsGrid from '@/components/charts/ChartsGrid.vue'
import BatteryChartsGrid from '@/components/charts/BatteryChartsGrid.vue'
import SingleCurrentChart from '@/components/charts/SingleCurrentChart.vue'
import DualAxisBatteryChart from '@/components/charts/DualAxisBatteryChart.vue'
import FormActivationDevice from '@/components/forms/create/device/formActivationDevice.vue'
import FloatingActionButtons from '@/components/operators/FloatingActionButtons.vue'

// Props
const props = defineProps({
  deviceId: {
    type: [String, Number],
    default: null
  },
  device: {
    type: Object,
    default: null
  },
  measurements: {
    type: Array,
    default: () => []
  },
  batteryPercentage: {
    type: Number,
    default: 0
  },
  recentMessages: {
    type: Array,
    default: () => []
  },
  currentMessages: {
    type: Array,
    default: () => []
  },
  batteryMessages: {
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
  latestDataPoints: {
    type: Object,
    default: () => ({})
  },
  deviceName: {
    type: String,
    default: 'Dispositivo IoT'
  },
  // Current tab props
  currentChartDataFragments: {
    type: Array,
    default: () => []
  },
  currentLatestDataPoints: {
    type: Object,
    default: () => ({})
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
  batteryChartDataFragments: {
    type: Array,
    default: () => []
  },
  batteryLatestDataPoints: {
    type: Object,
    default: () => ({})
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
  },
  // Device data for all measurements (keyed by measurement unit)
  measurementDevices: {
    type: Object,
    default: () => ({})
  },
  measurementMessages: {
    type: Object,
    default: () => ({})
  }
})

// Inject icons
const icons = inject('icons', {})
const loaded = ref(false)
// Router
const route = useRoute()

// Responsive view
const { isMobile, isTablet, isDesktop } = useResponsiveView()

// Component state
const isMounted = ref(false)
const measurements = ref(props.measurements && props.measurements.length > 0 ? props.measurements : null)
const measurementsLoading = ref(false)
const measurementsError = ref(null)
// Device fetch state (used by fetchDevice)
const loading = ref(false)
const error = ref(null)
const deviceDetails = ref(null) // store fetched device details (used by activation form)

// Comparison tab state
const selectedMeasurement1 = ref('')
const selectedMeasurement2 = ref('')
const selectedChannel1 = ref('')
const selectedChannel2 = ref('')

// Comparison chart filters state (persisted)
const comparisonFilters = ref({
  start: format(subDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"),
  end: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  step: 100
})

// Watch for props.measurements changes
watch(() => props.measurements, (newVal) => {
  if (newVal && newVal.length > 0) {
    measurements.value = newVal
    initializeDefaultSelections()
  }
})

// Watch for measurements changes to initialize selections
watch(measurements, (newVal) => {
  if (newVal && newVal.length > 0) {
    initializeDefaultSelections()
  }
})

// Fetch measurements from API
const fetchMeasurements = async (force = false) => {
  if (!force && measurements.value && measurements.value.length > 0) return
  
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
    
    // Check if it's a 404 error (No data found)
    const is404 = error.message?.includes('404') || 
                  error.status === 404 || 
                  error.response?.status === 404;

    if (is404) {
      // Treat 404 as "Success but empty" to show the friendly No Data state
      measurements.value = []
      measurementsError.value = null
    } else {
      measurementsError.value = error.message || 'Error al cargar las mediciones'
    }
  } finally {
    measurementsLoading.value = false
  }
}

const fetchDevice = async () => {
  if (!isMounted.value) {
    console.log('⏳ Component not ready, waiting...')
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    console.log('🔄 Fetching roles data...')
    
    const response = await API.get(API.DEVICE + route.params.device_id)
    // Normalize response shapes. Prefer object -> use as deviceDetails
    let result = null
    if (Array.isArray(response)) result = response[0] || null
    else if (response?.data) result = response.data
    else result = response

    deviceDetails.value = result
    console.log('✅ Device Retrieved (deviceDetails):', result)
    console.log('   is_active:', result?.is_active)
    
  } catch (err) {
    error.value = `Error al cargar roles: ${err.message}`
    console.error('❌ Error fetching roles:', err)
  } finally {
    loading.value = false
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
  if (!data || data.min == null || data.max == null || data.threshold == null) return 0
  
  const range = data.max - data.min
  if (range === 0) return 0
  const position = data.threshold - data.min
  const percentage = (position / range) * 100
  
  return Math.max(0, Math.min(100, percentage))
}

const calculateSafeZoneWidth = (data) => {
  if (!data || data.min == null || data.max == null || data.threshold == null) return 0
  
  const range = data.max - data.min
  if (range === 0) return 0
  const safeWidth = data.threshold // threshold is the buffer size
  
  return Math.max(0, Math.min(100, (safeWidth / range) * 100))
}

const calculateWarningValue = (data) => {
  if (!data || data.min == null || data.max == null || data.threshold == null) return data?.min ?? 0
  
  // Warning zone ends at max - threshold
  return data.max - data.threshold
}

const calculateWarningZoneWidth = (data) => {
  if (!data || data.min == null || data.max == null || data.threshold == null) return 0
  
  const range = data.max - data.min
  if (range === 0) return 0
  const warningStart = data.threshold
  const warningEnd = data.max - data.threshold
  const warningWidth = warningEnd - warningStart
  
  return Math.max(0, Math.min(100, (warningWidth / range) * 100))
}

const calculateDangerZoneWidth = (data) => {
  if (!data || data.min == null || data.max == null || data.threshold == null) return 0
  
  const range = data.max - data.min
  if (range === 0) return 0
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

// Helper function to get the appropriate chart grid component based on the unit
const getComponentForUnit = (unit) => {
  const profile = getProfileByValue(unit);
  
  // If the profile says it has 2 axes, use BatteryChartsGrid (which handles dual-axis)
  if (profile && profile.axes === 2) {
    return BatteryChartsGrid;
  }
  
  // Default to standard ChartsGrid for single-axis or unknown types
  return ChartsGrid;
};

// Helper function to get chart data for dynamic measurements
const getMeasurementChartData = (measurementUnit) => {
  // This function maps measurement units to their corresponding chart data
  // You can extend this to match specific measurement types with their data sources
  
  if (!measurementUnit) return []
  
  const unitLower = measurementUnit.toLowerCase()
  
  // Map common measurement types to existing chart data
  // You can extend this mapping as needed
  const chartDataMap = {
    'voltage': props.chartDataFragments || [],
    'voltaje': props.chartDataFragments || [],
    'current': props.currentChartDataFragments || [],
    'corriente': props.currentChartDataFragments || [],
    'battery': props.batteryChartDataFragments || [],
    'batería': props.batteryChartDataFragments || [],
    'bateria': props.batteryChartDataFragments || [],
  }
  
  // Return matching chart data or empty array for new measurement types
  return chartDataMap[unitLower] || []
}

// Helper function to get latest data points for dynamic measurements
const getMeasurementLatestDataPoints = (measurementUnit) => {
  if (!measurementUnit) return {}
  
  const unitLower = measurementUnit.toLowerCase()
  
  const latestDataMap = {
    'voltage': props.latestDataPoints || {},
    'voltaje': props.latestDataPoints || {},
    'current': props.currentLatestDataPoints || {},
    'corriente': props.currentLatestDataPoints || {},
    'battery': props.batteryLatestDataPoints || {},
    'batería': props.batteryLatestDataPoints || {},
    'bateria': props.batteryLatestDataPoints || {},
  }
  
  return latestDataMap[unitLower] || {}
}

// Helper function to get recent messages for dynamic measurements
const getMeasurementRecentMessages = (measurementUnit) => {
  if (!measurementUnit) return []
  
  const unitLower = measurementUnit.toLowerCase()
  
  const messagesMap = {
    'voltage': props.recentMessages || [],
    'voltaje': props.recentMessages || [],
    'current': props.currentMessages || [],
    'corriente': props.currentMessages || [],
    'battery': props.batteryMessages || [],
    'batería': props.batteryMessages || [],
    'bateria': props.batteryMessages || [],
  }
  
  return messagesMap[unitLower] || props.measurementMessages[unitLower] || []
}

// Helper function to get device data for a specific measurement
const getMeasurementDevice = (measurement) => {
  if (!measurement) return null
  
  // measurement.unit already contains the processor type (e.g., 'voltage', 'current', 'battery')
  const measurementType = measurement.unit?.toLowerCase()
  
  // Check if we have device data for this measurement type
  if (measurementType && props.measurementDevices[measurementType]) {
    return props.measurementDevices[measurementType]
  }
  
  // Fallback to main device if no specific device data found
  return props.device
}

onMounted(() => {
  // mark component as mounted first so helper methods can run immediately
  isMounted.value = true

  // then fetch device / measurements
  fetchDevice()
  fetchMeasurements().then(() => {
    // Initialize default selections after measurements are loaded
    initializeDefaultSelections()
  })
  loaded.value = true
})

// Watch for device ID changes and refetch
watch(() => route.params.device_id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    measurements.value = []
    fetchDevice()
    fetchMeasurements(true)
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
  fetchMeasurements(true)
}

// Set initial data for measurement editing (like TableApplications.vue)
const setMeasurementInitialData = (measurement) => {
  return {
    icon: measurement.icon,
    measurement_id: measurement.id,
    unit: measurement.unit,
    ref: measurement.ref,
    min: measurement.min,
    max: measurement.max,
    threshold: measurement.threshold
  }
  console.log('Initial data for measurement:', measurement)
}

// Helper functions for measurement comparison
const getAvailableMeasurements = () => {
  if (!measurements.value || measurements.value.length === 0) return []
  return measurements.value
}

const initializeDefaultSelections = () => {
  if (!measurements.value || measurements.value.length < 2) return
  
  // Auto-select first two measurements if nothing selected
  if (!selectedMeasurement1.value && !selectedMeasurement2.value) {
    // Try to find voltage and temperature first
    const voltage = measurements.value.find(m => 
      m.unit?.toLowerCase() === 'voltage' || m.unit?.toLowerCase() === 'voltaje'
    )
    const temperature = measurements.value.find(m => 
      m.unit?.toLowerCase() === 'temperature' || m.unit?.toLowerCase() === 'temperatura'
    )
    
    if (voltage && temperature) {
      selectedMeasurement1.value = voltage.unit.toLowerCase()
      selectedMeasurement2.value = temperature.unit.toLowerCase()
    } else {
      // Just use the first two available
      selectedMeasurement1.value = measurements.value[0].unit?.toLowerCase() || ''
      if (measurements.value.length > 1) {
        selectedMeasurement2.value = measurements.value[1].unit?.toLowerCase() || ''
      }
    }
  }
}

const onMeasurementSelectionChange = () => {
  console.log('📊 Measurement selection changed:', {
    measurement1: selectedMeasurement1.value,
    measurement2: selectedMeasurement2.value
  })
}

const handleComparisonFiltersChange = (newFilters) => {
  console.log('📅 Comparison filters updated:', newFilters)
  comparisonFilters.value = { ...newFilters }
}
</script>

<style scoped>
/* Scrollable Tab Bar */
.tabs-device-measurements ion-tab-bar {
  overflow-x: auto;
  overflow-y: hidden;
  display: flex;
  flex-wrap: nowrap;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: var(--ion-color-medium) transparent;
  padding: 0;
}

/* Mobile: align tabs to start for proper scrolling */
@media (max-width: 768px) {
  .tabs-device-measurements ion-tab-bar {
    justify-content: flex-start;
  }
}

/* Desktop: center tabs when they fit */
@media (min-width: 769px) {
  .tabs-device-measurements ion-tab-bar {
    justify-content: center;
    gap: 12px;
  }
}

.tabs-device-measurements ion-tab-bar::-webkit-scrollbar {
  height: 4px;
}

.tabs-device-measurements ion-tab-bar::-webkit-scrollbar-track {
  background: transparent;
}

.tabs-device-measurements ion-tab-bar::-webkit-scrollbar-thumb {
  background-color: var(--ion-color-medium);
  border-radius: 2px;
}

.tabs-device-measurements ion-tab-button {
  flex: 0 0 auto;
  min-width: 80px;
  max-width: 150px;
  margin: 0;
}

.tabs-device-measurements ion-tab-button:first-child {
  margin-left: 0;
}

.tabs-device-measurements ion-tab-button:last-child {
  margin-right: 0;
}

.tab-content {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Measurements Tab Styles */
.measurements-container {
  width: 100%;
  max-width: 1400px;
  margin: 1.5rem auto;
  padding: 0 1rem;
  box-sizing: border-box;
}

.measurements-container.desktop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 350px), 1fr));
  gap: 1.5rem;
}

.measurements-container.mobile-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0 0.5rem;
}

.measurement-card {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  overflow: hidden;
  margin-bottom: 0;
}

.measurement-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.measurement-card ion-card-header {
  padding: 1.25rem 1.5rem;
  background: linear-gradient(135deg, rgba(var(--ion-color-primary-rgb), 0.15) 0%, rgba(var(--ion-color-primary-rgb), 0.05) 100%);
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



.error-container h2 {
  color: var(--ion-color-dark);
  font-size: 1.25rem;
  margin: 1rem 0 0.5rem;
  font-weight: 600;
}

.error-message {
  color: var(--ion-color-danger);
  background: rgba(var(--ion-color-danger-rgb), 0.05);
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  margin: 1rem 0 2rem;
  font-size: 0.9rem;
  max-width: 90%;
  line-height: 1.4;
  border: 1px dashed rgba(var(--ion-color-danger-rgb), 0.3);
}

.error-container ion-icon {
  font-size: 3rem;
  opacity: 0.8;
}

.no-data h2 {
  color: var(--ion-color-dark);
  font-size: 1.25rem;
  margin: 1rem 0 0.5rem;
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
  .tab-content {
    padding: 0;
    gap: 1rem;
    width: 100%;
  }

  .measurements-container {
    margin: 0;
    padding: 0.5rem;
    width: 100%;
  }

  .measurements-container.mobile-stack,
  .measurements-container.desktop-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.5rem;
  }

  .measurement-card {
    border-radius: 12px;
    margin-bottom: 0;
    width: 100%;
  }

  .measurement-card ion-card-header {
    padding: 0.875rem;
  }

  .card-header-content {
    flex-direction: row;
    align-items: center;
    gap: 0.75rem;
  }

  .card-icon-wrapper {
    width: 48px;
    height: 48px;
    min-width: 48px;
    border-radius: 12px;
  }

  .card-icon-wrapper ion-icon {
    font-size: 24px;
  }

  .card-title-section {
    width: auto;
    flex: 1;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  .measurement-card ion-card-title {
    font-size: 1rem;
    font-weight: 600;
  }

  .measurement-card ion-card-content {
    padding: 0.875rem;
  }

  .measurements-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .measurement-item {
    padding: 0.75rem;
    gap: 0.5rem;
  }

  .measurement-icon {
    width: 32px;
    height: 32px;
    min-width: 32px;
    border-radius: 8px;
  }

  .measurement-icon ion-icon {
    font-size: 18px;
  }

  .measurement-info {
    flex: 1;
    min-width: 0;
  }

  .measurement-label {
    font-size: 0.7rem;
  }

  .measurement-value {
    font-size: 1rem;
    font-weight: 600;
  }

  .unit-text {
    font-size: 0.75rem;
  }

  .range-visualization {
    padding: 0.75rem;
    margin-top: 0.75rem;
  }

  .range-bar {
    height: 6px;
    margin-bottom: 0.75rem;
  }

  .range-labels {
    font-size: 0.65rem;
    height: 20px;
  }

  .range-label {
    font-size: 0.65rem;
    top: 6px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .measurements-container.desktop-grid {
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
    gap: 1rem;
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

/* Dynamic Measurement Detail Styles */
.measurement-detail-card,
.measurement-config-card {
  margin: 1rem 0;
}

.charts-section {
  margin: 2rem 0;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.waiting-data-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  background: var(--ion-color-light);
  border-radius: 12px;
  border: 2px dashed var(--ion-color-medium);
  text-align: center;
}

.waiting-data-card ion-icon {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.waiting-data-card p {
  color: var(--ion-color-dark);
  font-size: 1rem;
  margin: 0.5rem 0;
}

.waiting-data-card .hint-text {
  color: var(--ion-color-medium);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.additional-info {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--ion-color-light-shade);
}

.additional-info h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--ion-color-medium);
}

.info-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ion-color-dark);
}

.action-buttons {
  margin-top: 1rem;
  padding: 0 1rem;
}

.action-buttons ion-button {
  margin-bottom: 0.5rem;
}

/* Comparison Tab Styles */
.measurement-selector-card {
  margin: 1rem 0;
  background: linear-gradient(135deg, rgba(var(--ion-color-primary-rgb), 0.05) 0%, rgba(var(--ion-color-primary-rgb), 0.02) 100%);
  border: 1px solid rgba(var(--ion-color-primary-rgb), 0.1);
}

.measurement-selector-card ion-card-header {
  padding-bottom: 0.5rem;
}

.measurement-selector-card ion-card-title {
  font-size: 1.2rem;
  font-weight: 600;
}

.measurement-selector-card ion-card-subtitle {
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.selector-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1.5rem;
  align-items: center;
  margin: 1rem 0;
}

.selector-grid.is-mobile {
  grid-template-columns: 1fr;
  gap: 1rem;
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.channel-selector-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.channel-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--ion-color-medium);
  min-width: 45px;
}

.channel-select-inline {
  padding: 0.5rem;
  border: 1px solid var(--ion-color-light-shade);
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  color: var(--ion-color-dark);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 100px;
}

.channel-select-inline:hover {
  border-color: var(--ion-color-primary);
}

.channel-select-inline:focus {
  outline: none;
  border-color: var(--ion-color-primary);
  box-shadow: 0 0 0 2px rgba(var(--ion-color-primary-rgb), 0.1);
}

.selector-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ion-color-dark);
  margin-bottom: 0.25rem;
}

.measurement-select {
  padding: 0.75rem;
  border: 2px solid var(--ion-color-light-shade);
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  color: var(--ion-color-dark);
  cursor: pointer;
  transition: all 0.2s ease;
}

.measurement-select:hover {
  border-color: var(--ion-color-primary);
}

.measurement-select:focus {
  outline: none;
  border-color: var(--ion-color-primary);
  box-shadow: 0 0 0 3px rgba(var(--ion-color-primary-rgb), 0.1);
}

.measurement-select option:disabled {
  color: var(--ion-color-medium);
}

.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--ion-color-primary);
  padding: 0 1rem;
  align-self: flex-end;
  margin-bottom: 0.5rem;
}

.vs-divider span {
  background: linear-gradient(135deg, var(--ion-color-primary), var(--ion-color-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.info-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(var(--ion-color-primary-rgb), 0.05);
  border-radius: 8px;
  font-size: 0.875rem;
  color: var(--ion-color-medium);
}

.info-message ion-icon {
  color: var(--ion-color-primary);
  font-size: 1.25rem;
}

.instructions-card {
  margin: 1rem 0;
  background: linear-gradient(135deg, rgba(var(--ion-color-primary-rgb), 0.05) 0%, rgba(var(--ion-color-primary-rgb), 0.02) 100%);
}

.instructions-card ion-card-header {
  padding-bottom: 0.5rem;
}

.instructions-card ion-card-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.instructions-card p {
  margin: 0.5rem 0;
  line-height: 1.5;
}

.instructions-card strong {
  color: var(--ion-color-primary);
  font-weight: 600;
}

.warning-card {
  margin: 2rem 0;
  background: var(--ion-color-step-50, #f9f9f9);
  border-left: 6px solid var(--ion-color-warning);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.error-card {
  margin: 2rem 0;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(var(--ion-color-danger-rgb), 0.08);
}

.no-data-card {
  margin: 2rem 0;
  background: var(--ion-color-step-50, #f9f9f9);
  border-left: 6px solid var(--ion-color-medium);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.no-data-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  text-align: center;
  background: var(--ion-color-light, #f4f5f8);
  border-radius: 20px;
  margin: 2rem 0;
  border: 2px dashed var(--ion-color-step-200, #cccccc);
}

.empty-icon {
  font-size: 5rem;
  color: var(--ion-color-medium);
  margin-bottom: 1.5rem;
  opacity: 0.4;
}

.no-data-empty-state h2 {
  color: var(--ion-color-dark);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.no-data-empty-state p {
  color: var(--ion-color-step-600, #666666);
  font-size: 1.1rem;
  margin: 0 0 2rem 0;
  max-width: 300px;
}

.warning-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  gap: 1rem;
}

.warning-content ion-icon {
  color: var(--ion-color-warning);
  font-size: 48px;
}

.warning-content p {
  color: var(--ion-color-dark);
  font-size: 1rem;
  margin: 0;
}
</style>

