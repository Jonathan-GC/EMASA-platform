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
import { es } from 'date-fns/locale'
import { IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonButton, IonIcon } from '@ionic/vue'
import { refreshOutline } from 'ionicons/icons'

/**
 * VoltageChart Component
 * Renders a single voltage chart using native Chart.js
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
  onHover: (event, activeElements) => {
    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
  },
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  hover: {
    mode: 'index',
    intersect: false,
    animationDuration: 0
  },
  elements: {
    line: {
      tension: 0, // Disable Bezier curves to prevent segment calculation errors
      spanGaps: true // Prevent crashes if points are pruned during draw
    },
    point: {
      radius: 0, // Performance: don't draw points
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
        title: (context) => context[0]?.parsed?.x ? format(new Date(context[0].parsed.x), 'HH:mm:ss.SSS', { locale: es }) : '',
        label: (context) => `Voltaje: ${context.parsed.y.toFixed(3)}V`
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
      },
      limits: {
        x: {
            minDelay: 4000,
            maxDelay: 4000,
            minDuration: 1000,
            maxDuration: 50000
          }
      }
    }
  },
  scales: {
    x: {
      type: 'realtime',
      adapters: {
        date: {
          locale: es
        }
      },
      realtime: {
        duration: 30000,
        refresh: 1000,
        delay: 10000,
        ttl: 60000,
        onRefresh: (chart) => {
          if (streamingBuffer.length > 0) {
            if (chart.data.datasets[0]) {
              chart.data.datasets[0].data.push(...streamingBuffer.map(p => toRaw(p)))
            }
            streamingBuffer.length = 0
            updateSampleCount()
          }
        }
      },
      title: { display: true, text: 'Tiempo' }
    },
    y: {
      min: props.yAxisMin,
      max: props.yAxisMax,
      title: { display: true, text: 'Voltaje (V)' },
      grid: { color: 'rgba(0, 0, 0, 0.1)' }
    }
  }
}))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->