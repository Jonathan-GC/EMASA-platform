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
        <Line
          ref="chartRef"
          :data="chartData"
          :options="chartOptions"
        />
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import { format } from 'date-fns'

/**
 * VoltageChart Component - Single voltage chart display
 * Responsibility: Render a single voltage chart with proper configuration
 * Optimized to update chart data without re-rendering with progressive line drawing
 */
const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 0
  },
  title: {
    type: String,
    default: ''
  },
  deviceName: {
    type: String,
    default: 'Dispositivo IoT'
  },
  yAxisMin: {
    type: Number,
    default: null
  },
  yAxisMax: {
    type: Number,
    default: null
  }
})

const chartRef = ref(null)
const sampleCount = ref(0)

// Update sample count without triggering re-render
const updateSampleCount = () => {
  sampleCount.value = props.chartData.datasets[0]?.data?.length || 0
}

// Watch for data changes and update chart directly
watch(() => props.chartData, (newData) => {
  if (chartRef.value?.chart) {
    // Update chart data directly without re-rendering or animation
    chartRef.value.chart.data.datasets = newData.datasets
    chartRef.value.chart.update('none') // 'none' mode = no animation
    updateSampleCount()
  }
}, { deep: false })

onMounted(() => {
  updateSampleCount()
})

// Chart options configuration
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  animation: false,
  plugins: {
    title: {
      display: true,
      text: `Sensor ${props.index + 1} - ${props.deviceName}`
    },
    legend: {
      display: true
    },
    tooltip: {
      callbacks: {
        title: function(context) {
          if (context[0]?.parsed?.x) {
            return format(new Date(context[0].parsed.x), 'HH:mm:ss.SSS')
          }
          return ''
        },
        label: function(context) {
          return `Voltaje: ${context.parsed.y.toFixed(3)}V`
        }
      }
    }
  },
  scales: {
    x: {
      type: 'time',
      time: {
        displayFormats: {
          millisecond: 'HH:mm:ss.SSS',
          second: 'HH:mm:ss',
          minute: 'HH:mm'
        }
      },
      title: {
        display: true,
        text: 'Tiempo'
      }
    },
    y: {
      beginAtZero: false,
      min: props.yAxisMin,
      max: props.yAxisMax,
      title: {
        display: true,
        text: 'Voltaje (V)'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      }
    }
  },
  elements: {
    line: {
      tension: 0.4 // Smooth curve for the line
    },
    point: {
      radius: 0,
      hitRadius: 10,
      hoverRadius: 5
    }
  }
}))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->