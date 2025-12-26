<template>
  <ion-card class="chart-fragment">
    <ion-card-header>
      <ion-card-title>
        {{ title || `Sensor ${index + 1}` }} 
        ({{ sampleCount }} muestras)
      </ion-card-title>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-container">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted, toRaw, markRaw } from 'vue'
import { Chart } from 'chart.js'
import { format } from 'date-fns'
import { IonCard, IonCardHeader, IonCardTitle, IonCardContent } from '@ionic/vue'

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
const streamingBuffer = []

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
      tension: 0, // Disable Bezier curves to prevent segment calculation errors
      spanGaps: true // Prevent crashes if points are pruned during draw
    },
    point: {
      radius: 0, // Performance: don't draw points
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
        delay: 3250,
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