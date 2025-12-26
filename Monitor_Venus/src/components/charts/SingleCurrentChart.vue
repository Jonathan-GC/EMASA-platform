<template>
  <ion-card class="chart-container">
    <ion-card-header>
      <div class="header-content">
        <ion-card-title>
          📊 Mediciones de Corriente - {{ deviceName }}
        </ion-card-title>
      </div>
      <ion-card-subtitle>
        {{ sampleCount }} muestras
      </ion-card-subtitle>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-wrapper">
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
import { IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent, IonButton, IonIcon } from '@ionic/vue'
import { refreshOutline } from 'ionicons/icons'

/**
 * SingleCurrentChart Component
 * Renders current measurements using native Chart.js
 * for high-performance streaming and stability.
 */
const props = defineProps({
  chartData: { type: Object, required: true },
  latestDataPoints: { type: Object, default: () => ({}) },
  chartKey: { type: Number, default: 0 },
  deviceName: { type: String, default: 'Dispositivo IoT' },
  yAxisMin: { type: Number, default: null },
  yAxisMax: { type: Number, default: null }
})

const canvasRef = ref(null)
const chartInstance = ref(null)
const sampleCount = ref(0)
const isZoomed = ref(false)
const streamingBufferMap = {}

// Initialize non-reactive data structure for Chart.js
const localChartData = markRaw({
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

// Watch for incoming points and buffer them by channel
watch(() => props.latestDataPoints, (newPointsMap) => {
  if (newPointsMap) {
    Object.entries(newPointsMap).forEach(([channelIndex, points]) => {
      if (!streamingBufferMap[channelIndex]) {
        streamingBufferMap[channelIndex] = []
      }
      streamingBufferMap[channelIndex].push(...points)
    })
  }
}, { deep: false })

onMounted(() => {
  if (canvasRef.value) {
    chartInstance.value = new Chart(canvasRef.value, {
      type: 'line',
      data: localChartData,
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
      text: `Corriente - ${props.deviceName}`
    },
    legend: { display: true },
    tooltip: {
      animation: false,
      callbacks: {
        title: (context) => context[0]?.parsed?.x ? format(new Date(context[0].parsed.x), 'HH:mm:ss.SSS') : '',
        label: (context) => `Corriente: ${context.parsed.y.toFixed(3)}A`
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
          let hasUpdates = false
          Object.entries(streamingBufferMap).forEach(([channelIndex, points]) => {
            const idx = parseInt(channelIndex)
            if (chart.data.datasets[idx] && points.length > 0) {
              chart.data.datasets[idx].data.push(...points.map(p => toRaw(p)))
              points.length = 0
              hasUpdates = true
            }
          })
          if (hasUpdates) updateSampleCount()
        }
      },
      title: { display: true, text: 'Tiempo' }
    },
    y: {
      min: props.yAxisMin,
      max: props.yAxisMax,
      title: { display: true, text: 'Corriente (A)' },
      grid: { color: 'rgba(0, 0, 0, 0.1)' }
    }
  }
}))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->