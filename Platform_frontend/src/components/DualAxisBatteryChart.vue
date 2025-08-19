<template>
  <ion-card class="chart-container">
    <ion-card-header>
      <ion-card-title>
        📊 Mediciones de Batería - {{ deviceName }}
      </ion-card-title>
      <ion-card-subtitle>
        {{ getTotalSamples() }} muestras | Voltaje y Porcentaje
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

const getTotalSamples = () => {
  return props.chartData.datasets[0]?.data?.length || 0
}

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
      text: `Mediciones de Batería - ${props.deviceName}`
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
          if (context.datasetIndex === 0) {
            return `Voltaje: ${context.parsed.y.toFixed(2)}V`
          } else {
            return `Porcentaje: ${context.parsed.y}%`
          }
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
    'y-left': {
      position: 'left',
      beginAtZero: false,
      title: {
        display: true,
        text: 'Voltaje (V)'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      }
    },
    'y-right': {
      position: 'right',
      min: 0,
      max: 100,
      title: {
        display: true,
        text: 'Porcentaje (%)'
      },
      grid: {
        drawOnChartArea: false
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #4ade80;
}

.chart-wrapper {
  height: 400px;
  position: relative;
}

@media (max-width: 768px) {
  .chart-wrapper {
    height: 300px;
  }
}
</style>
