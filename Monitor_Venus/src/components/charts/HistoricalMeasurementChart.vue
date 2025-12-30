<template>
  <ion-card class="historical-chart-card">
    <ion-card-header>
      <div class="header-container">
        <div class="title-section">
          <ion-card-title>{{ title }}</ion-card-title>
          <ion-card-subtitle>{{ subtitle }}</ion-card-subtitle>
        </div>
        <div class="filter-section" :class="{ 'is-mobile': isMobile }">
          <div class="date-filters">
            <div class="filter-item">
              <input type="datetime-local" v-model="filters.start" @change="fetchData" />
            </div>
            <div class="filter-item">
              <input type="datetime-local" v-model="filters.end" @change="fetchData" />
            </div>
          </div>
          <div class="other-filters">
            <div class="filter-item">
              <select v-model="filters.measurement_type" @change="fetchData">
                <option v-for="type in measurementTypes" :key="type" :value="type">
                  {{ capitalize(type) }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <input type="number" v-model.number="filters.step" @change="fetchData" min="1" max="1000" placeholder="Steps" style="width: 80px;" />
            </div>
          </div>
        </div>
      </div>
    </ion-card-header>

    <ion-card-content :class="{ 'is-mobile-content': isMobile }">
      <div v-if="loading" class="loading-overlay">
        <ion-spinner name="crescent"></ion-spinner>
      </div>
      <div class="chart-container">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { ref, onMounted, watch, reactive, computed } from 'vue'
import { 
  IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, 
  IonCardContent, IonSpinner 
} from '@ionic/vue'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'
import API from '@/utils/api/api.js'
import { format, subDays } from 'date-fns'
import { useResponsiveView } from '@/composables/useResponsiveView.js'

Chart.register(...registerables)

const props = defineProps({
  deviceId: {
    type: [String, Number],
    required: true
  },
  initialType: {
    type: String,
    default: 'voltage'
  },
  availableMeasurements: {
    type: Array,
    default: () => []
  }
})

const { isMobile } = useResponsiveView()
const canvasRef = ref(null)
let chartInstance = null

const loading = ref(false)
const title = ref('Total Visitors')
const subtitle = ref('Total for the last 3 months')

const measurementTypes = computed(() => {
  const types = new Set(['voltage', 'current', 'battery'])
  if (props.availableMeasurements && props.availableMeasurements.length > 0) {
    props.availableMeasurements.forEach(m => {
      if (m.unit) types.add(m.unit.toLowerCase())
    })
  }
  return Array.from(types)
})

const filters = reactive({
  start: format(subDays(new Date(), 90), "yyyy-MM-dd'T'HH:mm"),
  end: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  measurement_type: props.initialType,
  step: 100
})

const capitalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : ''

const fetchData = async () => {
  if (!props.deviceId) return
  
  loading.value = true
  try {
    const params = new URLSearchParams({
      start: new Date(filters.start).toISOString(),
      end: new Date(filters.end).toISOString(),
      measurement_type: filters.measurement_type,
      steps: filters.step
    })

    const url = `${API.DEVICE_HISTORICAL_MEASUREMENTS(props.deviceId)}?${params.toString()}`
    const response = await API.get(url)
    
    let data = []
    if (response && response.data) {
      data = response.data
    } else if (Array.isArray(response)) {
      data = response
    }
    
    updateChart(data)
    
    // Update title based on measurement type
    title.value = `Historico de ${capitalize(filters.measurement_type)}`
    subtitle.value = `Datos desde ${format(new Date(filters.start), 'MMM dd')} hasta ${format(new Date(filters.end), 'MMM dd')}`
  } catch (error) {
    console.error('Error fetching historical data:', error)
  } finally {
    loading.value = false
  }
}

const updateChart = (data) => {
  if (!chartInstance) return

  const datasets = []
  
  if (data && data.length > 0) {
    // Group data by channel
    const channelGroups = {}
    data.forEach(item => {
      const ch = item.channel || 'default'
      if (!channelGroups[ch]) channelGroups[ch] = []
      
      const timestamp = new Date(item.timestamp || item.time || item.arrival_date)
      if (isNaN(timestamp.getTime())) return // Skip invalid dates
      
      const val = item.avg !== undefined ? item.avg : (item.value !== undefined ? item.value : item.values?.[ch])
      
      channelGroups[ch].push({
        x: timestamp.getTime(),
        y: val !== undefined && val !== null ? Number(val) : null,
        min: item.min,
        max: item.max
      })
    })

    // Sort each group by timestamp to ensure correct line rendering
    Object.keys(channelGroups).forEach(ch => {
      channelGroups[ch].sort((a, b) => a.x - b.x)
    })

    // Create datasets for each channel
    Object.keys(channelGroups).forEach((ch, index) => {
      const color = getChartColor(index)
      datasets.push({
        label: ch === 'default' ? capitalize(filters.measurement_type) : `Channel ${ch}`,
        data: channelGroups[ch],
        parsing: false,
        borderColor: color,
        backgroundColor: (context) => {
          const chart = context.chart;
          const {ctx, chartArea} = chart;
          if (!chartArea || !ctx) return 'transparent';
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, color.replace('1)', '0.4)'));
          gradient.addColorStop(1, color.replace('1)', '0)'));
          return gradient;
        },
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
      })
    })
  }

  chartInstance.data.datasets = datasets
  chartInstance.update()
}

const getChartColor = (index) => {
  const colors = [
    'rgba(59, 130, 246, 1)', // Blue
    'rgba(16, 185, 129, 1)', // Green
    'rgba(246, 59, 59, 1)',  // Red
    'rgba(234, 179, 8, 1)',   // Yellow
    'rgba(139, 92, 246, 1)'  // Purple
  ]
  return colors[index % colors.length]
}

onMounted(() => {
  const ctx = canvasRef.value.getContext('2d')
  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      scales: {
        x: {
          type: 'time',
          realtime: false,
          time: {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MMM dd',
              month: 'MMM yyyy'
            }
          },
          grid: {
            display: false,
            drawBorder: false
          },
          ticks: {
            color: '#9ca3af',
            font: {
              size: 11
            }
          }
        },
        y: {
          grid: {
            color: 'rgba(156, 163, 175, 0.05)',
            drawBorder: false
          },
          ticks: {
            color: '#9ca3af',
            font: {
              size: 11
            }
          }
        }
      },
      plugins: {
        streaming: false,
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#000',
          titleColor: '#9ca3af',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
          usePointStyle: true,
          callbacks: {
            title: (context) => {
              if (!context || !context[0]) return ''
              return format(new Date(context[0].parsed.x), 'MMM dd, HH:mm')
            },
            label: (context) => {
              const point = context.raw;
              if (!point) return ''
              let label = `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
              if (point.min !== undefined && point.max !== undefined) {
                label += ` (Min: ${point.min}, Max: ${point.max})`;
              }
              return label;
            }
          }
        }
      }
    }
  })

  fetchData()
})

watch(() => props.deviceId, () => {
  fetchData()
})
</script>

<style scoped>



.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 8px 4px;
}

.title-section ion-card-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.title-section ion-card-subtitle {
  font-size: 0.875rem;
  margin-top: 4px;
}

.filter-section {
  display: flex;
  gap: 12px;
  align-items: center;
  background: var(--ion-color-light, rgba(255, 255, 255, 0.03));
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid var(--ion-border-color, rgba(255, 255, 255, 0.05));
  transition: all 0.3s ease;
}

.filter-section.is-mobile {
  flex-direction: column;
  align-items: stretch;
  gap: 16px;
  padding: 16px;
}

.date-filters {
  display: flex;
  gap: 8px;
  border-right: 1px solid var(--ion-border-color, rgba(255, 255, 255, 0.1));
  padding-right: 12px;
}

.is-mobile .date-filters {
  flex-direction: column;
  border-right: none;
  padding-right: 0;
  border-bottom: 1px solid var(--ion-border-color, rgba(255, 255, 255, 0.1));
  padding-bottom: 12px;
}

.other-filters {
  display: flex;
  gap: 12px;
}

.is-mobile .other-filters {
  justify-content: space-between;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.is-mobile .filter-item {
  width: 100%;
}

.filter-item label {
  display: none; /* Hide labels to match image */
}

.filter-item input, .filter-item select {
  background: var(--ion-background-color, transparent);
  border: 1px solid var(--ion-border-color, rgba(255, 255, 255, 0.1));
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.875rem;
  outline: none;
  transition: all 0.2s;
  color: var(--ion-text-color, #000);
}

.is-mobile .filter-item input, 
.is-mobile .filter-item select {
  width: 100%;
  height: 44px; /* Better touch target */
}

.filter-item input[type="datetime-local"] {
  min-width: 180px;
}

.is-mobile .filter-item input[type="datetime-local"] {
  min-width: 0;
}

.filter-item input:focus, .filter-item select:focus {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.is-mobile-content {
  padding-left: 8px;
  padding-right: 8px;
}

.chart-container {
  height: 350px;
  position: relative;
  margin-top: 20px;
}

.is-mobile .chart-container {
  height: 280px;
  margin-top: 10px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(17, 24, 39, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .title-section ion-card-title {
    font-size: 1.25rem;
  }

  .filter-section {
    width: 100%;
  }
}
</style>
