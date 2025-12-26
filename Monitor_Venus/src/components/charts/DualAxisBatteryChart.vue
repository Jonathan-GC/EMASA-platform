<template>
  <ion-card class="chart-container">
    <ion-card-header>
      <ion-card-title>
        📊 Mediciones de Batería - {{ deviceName }}
      </ion-card-title>
      <ion-card-subtitle>
        {{ sampleCount }} muestras | Voltaje y Porcentaje
      </ion-card-subtitle>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-wrapper">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted, toRaw, markRaw } from 'vue'
import { Chart } from 'chart.js'
import { format } from 'date-fns'
import { IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent } from '@ionic/vue'

/**
 * DualAxisBatteryChart Component
 * Renders a dual-axis battery chart (Voltage & Percentage) using native Chart.js
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

// Constants & State
const BATTERY_MIN_V = 10.5
const BATTERY_MAX_V = 13.2

const canvasRef = ref(null)
const chartInstance = ref(null)
const sampleCount = ref(0)
const streamingBuffer = []

// Initialize non-reactive data structure for Chart.js
const localChartData = markRaw({
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

// Watch for incoming points and buffer them
watch(() => props.latestDataPoints, (newPointsMap) => {
  if (newPointsMap) {
    const points = newPointsMap[1] || newPointsMap[0]
    if (points?.length > 0) {
      streamingBuffer.push(...points)
    }
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