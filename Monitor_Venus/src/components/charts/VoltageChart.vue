<template>
  <ion-card class="chart-fragment">
    <ion-card-header>
      <ion-card-title>
        {{ title || `Sensor ${index + 1}` }} 
        ({{ chartData.datasets[0]?.data?.length || 0 }} muestras)
      </ion-card-title>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-container">
        <Line
          :data="chartData"
          :options="chartOptions"
        />
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { format } from 'date-fns'

/**
 * VoltageChart Component - Single voltage chart display
 * Responsibility: Render a single voltage chart with proper configuration
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
  }
})

// Chart options configuration
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
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
      title: {
        display: true,
        text: 'Voltaje (V)'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      }
    }
  },
  animation: {
    duration: 200
  }
}))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->