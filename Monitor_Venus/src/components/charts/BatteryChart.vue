<template>
  <ion-card class="chart-fragment">
    <ion-card-header>
      <div class="header-content">
        <ion-card-title>
          {{ title || `Sensor ${index + 1}` }} 
          ({{ sampleCount }} muestras)
        </ion-card-title>
      </div>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-container">
        <canvas ref="canvasRef"></canvas>
        <ion-button 
          v-if="isZoomed" 
          fill="clear" 
          size="small" 
          @click="resetZoom"
          class="reset-zoom-btn"
        >
          <ion-icon slot="icon-only" :icon="refreshOutline"></ion-icon>
        </ion-button>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted, toRaw, markRaw } from 'vue'
import { Chart } from 'chart.js'
import { format } from 'date-fns'
import { IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonButton, IonIcon } from '@ionic/vue'
import { refreshOutline } from 'ionicons/icons'

/**
 * BatteryChart Component
 * Renders a dual-axis chart (Voltage & Percentage) using native Chart.js
 * for high-performance streaming and stability.
 */
const props = defineProps({
  chartData: { type: Object, required: true },
  latestDataPoints: { type: Array, default: () => [] },
  index: { type: Number, default: 0 },
  title: { type: String, default: '' },
  deviceName: { type: String, default: 'Dispositivo IoT' },
  yAxisMin: { type: Number, default: null },
  yAxisMax: { type: Number, default: null }
})

// Constants & State
const BATTERY_MIN_V = 10.5
const BATTERY_MAX_V = 13.2

const canvasRef = ref(null)
const chartInstance = ref(null)
const sampleCount = ref(0)
const isZoomed = ref(false)
const streamingBuffer = []

// Initialize non-reactive data structure for Chart.js
const localChartData = ref({
  datasets: props.chartData.datasets.map(ds => ({
    ...ds,
    data: [...ds.data]
  }))
})

// Helper: Convert voltage to percentage
const voltageToPercentage = (v) => {
  if (v <= BATTERY_MIN_V) return 0
  if (v >= BATTERY_MAX_V) return 100
  return Math.round(((v - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100)
}

// Helper: Update the sample count display
const updateSampleCount = () => {
  if (chartInstance.value) {
    sampleCount.value = chartInstance.value.data.datasets[0]?.data?.length || 0
  }
}

const resetZoom = () => {
  if (chartInstance.value) {
    chartInstance.value.resetZoom()
    isZoomed.value = false
  }
}

// Watch for chartData changes (e.g. from preload)
watch(() => props.chartKey, () => {
  if (chartInstance.value && props.chartData?.datasets) {
    props.chartData.datasets.forEach((ds, i) => {
      if (chartInstance.value.data.datasets[i]) {
        chartInstance.value.data.datasets[i].data = [...ds.data]
      }
    })
    chartInstance.value.update('none')
    updateSampleCount()
  }
}, { immediate: false })

// Watch for incoming points and buffer them for the next chart refresh cycle
watch(() => props.latestDataPoints, (points) => {
  if (points?.length > 0) {
    streamingBuffer.push(...points)
  }
}, { deep: false })

onMounted(() => {
  if (canvasRef.value) {
    chartInstance.value = new Chart(canvasRef.value, {
      type: 'line',
      data: toRaw(localChartData.value),
      options: chartOptions.value
    })
    updateSampleCount()
  }
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  interaction: {
    intersect: true,
    mode: 'nearest'
  },
  hover: {
    mode: 'nearest',
    intersect: true,
    animationDuration: 0
  },
  elements: {
    line: {
      tension: 0,
      spanGaps: true
    },
    point: {
      radius: 0,
      hitRadius: 10,
      hoverRadius: 5
    }
  },
  plugins: {
    title: {
      display: true,
      text: `${props.title || `Sensor ${props.index + 1}`} - ${props.deviceName}`
    },
    legend: { display: true },
    tooltip: {
      animation: false,
      callbacks: {
        title: (context) => context[0]?.parsed?.x ? format(new Date(context[0].parsed.x), 'HH:mm:ss.SSS') : '',
        label: (context) => {
          const isPercent = context.dataset.label.includes('%')
          return `${context.dataset.label}: ${context.parsed.y.toFixed(isPercent ? 1 : 3)}${isPercent ? '%' : 'V'}`
        }
      }
    },
    zoom: {
      pan: {
        enabled: true,
        mode: 'x',
        modifierKey: 'ctrl',
        onPanComplete: () => { isZoomed.value = true }
      },
      zoom: {
        wheel: {
          enabled: true,
        },
        pinch: {
          enabled: true
        },
        mode: 'x',
        onZoomComplete: () => { isZoomed.value = true }
      }
    }
  },
  scales: {
    x: {
      type: 'realtime',
      realtime: {
        duration: 30000,
        refresh: 1000,
        delay: 1000,
        ttl: 60000,
        onRefresh: (chart) => {
          if (streamingBuffer.length > 0) {
            streamingBuffer.forEach(point => {
              const rawPoint = toRaw(point)
              if (chart.data.datasets[0]) chart.data.datasets[0].data.push(rawPoint)
              if (chart.data.datasets[1]) {
                chart.data.datasets[1].data.push({
                  x: rawPoint.x,
                  y: voltageToPercentage(rawPoint.y)
                })
              }
            })
            streamingBuffer.length = 0
            updateSampleCount()
          }
        }
      },
      title: { display: true, text: 'Tiempo' }
    },
    'y-left': {
      position: 'left',
      min: props.yAxisMin,
      max: props.yAxisMax,
      title: { display: true, text: 'Voltaje (V)' },
      grid: { color: 'rgba(0, 0, 0, 0.1)' }
    },
    'y-right': {
      position: 'right',
      min: 0,
      max: 100,
      title: { display: true, text: 'Porcentaje (%)' },
      grid: { drawOnChartArea: false }
    }
  }
}))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->
