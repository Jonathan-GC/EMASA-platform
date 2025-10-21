<template>
  <ion-card class="chart-container">
    <ion-card-header>
      <ion-card-title>
        📊 Mediciones de Corriente - {{ deviceName }}
      </ion-card-title>
      <ion-card-subtitle>
        {{ chartData.datasets[0]?.data?.length || 0 }} muestras
      </ion-card-subtitle>
    </ion-card-header>
    <ion-card-content>
      <div class="chart-wrapper">
        <Line
          :data="chartData"
          :options="chartOptions"
          :key="chartKey"
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
 * SingleCurrentChart Component - Single current chart display
 * Responsibility: Render current measurements chart with proper configuration
 */
const props = defineProps({
  chartData: {
    type: Object,
    required: true
  },
  chartKey: {
    type: Number,
    default: 0
  },
  deviceName: {
    type: String,
    default: 'Dispositivo IoT'
  }
})

// Chart options configuration for current measurements
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
      text: `Mediciones de Corriente - ${props.deviceName}`
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
          return `Corriente: ${context.parsed.y.toFixed(3)}A`
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
        text: 'Corriente (A)'
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

<style scoped>
.chart-container {
  margin-top: 30px;
  background: white;
  border-radius: 8px;
  
}

.chart-wrapper {
  height: 400px;
  position: relative;
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .chart-wrapper {
    height: 300px;
  }
}
</style>
