<template>
  <ion-card class="combined-historical-chart-card">
    <ion-card-header>
      <div class="header-container">
        <div class="title-section">
          <ion-card-title>{{ title }}</ion-card-title>
          <ion-card-subtitle>{{ subtitle }}</ion-card-subtitle>
        </div>
        <div class="filter-section" :class="{ 'is-mobile': isMobile }">
          <div class="date-filters">
            <div class="filter-item">
              <input type="datetime-local" v-model="filters.start" :max="today" :min="yesterday" @change="fetchData" />
            </div>
            <div class="filter-item">
              <input type="datetime-local" v-model="filters.end" :max="today" :min="yesterday" @change="fetchData" />
            </div>
          </div>
          <div class="other-filters">
            <div class="filter-item">
              <input type="number" v-model.number="stepValue" @change="fetchData" min="1" max="300" placeholder="Steps" style="width: 80px;" />
            </div>
          </div>
        </div>
      </div>
    </ion-card-header>

    <ion-card-content :class="{ 'is-mobile-content': isMobile }">
      <div v-if="loading" class="loading-overlay">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando datos...</p>
      </div>
      <div class="chart-container">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch } from 'vue'
import { 
  IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, 
  IonCardContent, IonSpinner 
} from '@ionic/vue'
import { Chart, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'
import API from '@/utils/api/api.js'
import { format, subDays } from 'date-fns'
import { es } from 'date-fns/locale'
import { useResponsiveView } from '@/composables/useResponsiveView.js'

Chart.register(...registerables, annotationPlugin)

const props = defineProps({
  deviceId: {
    type: [String, Number],
    required: true
  },
  measurement1Type: {
    type: String,
    required: true
  },
  measurement2Type: {
    type: String,
    required: true
  },
  channel1: {
    type: String,
    default: ''
  },
  channel2: {
    type: String,
    default: ''
  },
  initialFilters: {
    type: Object,
    default: () => ({
      start: format(subDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"),
      end: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
      step: 100
    })
  }
})

const emit = defineEmits(['filters-changed'])

const { isMobile } = useResponsiveView()
const canvasRef = ref(null)
let chartInstance = null

const loading = ref(false)
const title = ref('Comparación de Mediciones')
const subtitle = ref('Últimos datos históricos')
const today = format(new Date(), "yyyy-MM-dd'T'HH:mm")
const yesterday = format(subDays(new Date(), 89), "yyyy-MM-dd'T'HH:mm")

const filters = reactive({
  start: props.initialFilters.start || format(subDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"),
  end: props.initialFilters.end || format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  step: props.initialFilters.step || 100
})

const stepValue = computed({
  get: () => filters.step,
  set: (val) => {
    filters.step = Math.min(Math.max(1, val), 300)
    emit('filters-changed', { ...filters })
  }
})

const capitalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : ''

const fetchData = async () => {
  if (!props.deviceId) return
  
  // Emit current filter state
  emit('filters-changed', { ...filters })
  
  loading.value = true
  try {
    const params1 = new URLSearchParams({
      start: new Date(filters.start).toISOString(),
      end: new Date(filters.end).toISOString(),
      measurement_type: props.measurement1Type,
      steps: filters.step
    })

    const params2 = new URLSearchParams({
      start: new Date(filters.start).toISOString(),
      end: new Date(filters.end).toISOString(),
      measurement_type: props.measurement2Type,
      steps: filters.step
    })

    // Add channel parameter for measurement 1 if provided
    if (props.channel1) {
      params1.append('channel', `ch${props.channel1}`)
    }

    // Add channel parameter for measurement 2 if provided
    if (props.channel2) {
      params2.append('channel', `ch${props.channel2}`)
    }

    const url1 = `${API.DEVICE_HISTORICAL_MEASUREMENTS(props.deviceId)}?${params1.toString()}`
    const url2 = `${API.DEVICE_HISTORICAL_MEASUREMENTS(props.deviceId)}?${params2.toString()}`

    console.log('📡 Fetching measurement 1:', props.measurement1Type, props.channel1 ? `(Channel ${props.channel1})` : '(All channels)')
    console.log('📡 Fetching measurement 2:', props.measurement2Type, props.channel2 ? `(Channel ${props.channel2})` : '(All channels)')

    // Make both API calls in parallel
    const [response1, response2] = await Promise.all([
      API.get(url1),
      API.get(url2)
    ])
    
    let data1 = Array.isArray(response1) ? response1 : (response1?.data || [])
    let data2 = Array.isArray(response2) ? response2 : (response2?.data || [])
    
    console.log('✅ Data fetched:', data1.length, 'points for', props.measurement1Type)
    console.log('✅ Data fetched:', data2.length, 'points for', props.measurement2Type)
    
    updateChart(data1, data2)
    
    // Update title
    const measurement1Label = `${capitalize(props.measurement1Type)}${props.channel1 ? ` (CH${props.channel1})` : ''}`
    const measurement2Label = `${capitalize(props.measurement2Type)}${props.channel2 ? ` (CH${props.channel2})` : ''}`
    title.value = `${measurement1Label} vs ${measurement2Label}`
    subtitle.value = `Datos desde ${format(new Date(filters.start), 'MMM dd', { locale: es })} hasta ${format(new Date(filters.end), 'MMM dd', { locale: es })}`
  } catch (error) {
    console.error('❌ Error fetching combined historical data:', error)
  } finally {
    loading.value = false
  }
}

const updateChart = (data1, data2) => {
  if (!chartInstance) return

  const datasets = []
  
  // Process first measurement
  if (data1 && data1.length > 0) {
    const channelGroups1 = processDataByChannel(data1, props.measurement1Type)
    const colors1 = ['rgba(59, 130, 246, 1)', 'rgba(16, 185, 129, 1)']
    
    Object.keys(channelGroups1).forEach((ch, index) => {
      const color = colors1[index % colors1.length]
      const channelLabel = ch !== 'default' ? ` ${ch}` : ''
      datasets.push({
        label: `${capitalize(props.measurement1Type)}${channelLabel}`,
        data: channelGroups1[ch],
        parsing: false,
        borderColor: color,
        backgroundColor: (context) => {
          const chart = context.chart;
          const {ctx, chartArea} = chart;
          if (!chartArea || !ctx) return 'transparent';
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, color.replace('1)', '0.3)'));
          gradient.addColorStop(1, color.replace('1)', '0)'));
          return gradient;
        },
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
        yAxisID: 'y1'
      })
    })
  }
  
  // Process second measurement
  if (data2 && data2.length > 0) {
    const channelGroups2 = processDataByChannel(data2, props.measurement2Type)
    const colors2 = ['rgba(234, 179, 8, 1)', 'rgba(139, 92, 246, 1)']
    
    Object.keys(channelGroups2).forEach((ch, index) => {
      const color = colors2[index % colors2.length]
      const channelLabel = ch !== 'default' ? ` ${ch}` : ''
      datasets.push({
        label: `${capitalize(props.measurement2Type)}${channelLabel}`,
        data: channelGroups2[ch],
        parsing: false,
        borderColor: color,
        backgroundColor: (context) => {
          const chart = context.chart;
          const {ctx, chartArea} = chart;
          if (!chartArea || !ctx) return 'transparent';
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, color.replace('1)', '0.3)'));
          gradient.addColorStop(1, color.replace('1)', '0)'));
          return gradient;
        },
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
        yAxisID: 'y2'
      })
    })
  }

  chartInstance.data.datasets = datasets
  chartInstance.update()
}

const processDataByChannel = (data, measurementType) => {
  const channelGroups = {}
  
  data.forEach(item => {
    const ch = item.channel || 'default'
    if (!channelGroups[ch]) channelGroups[ch] = []
    
    let rawTime = item.timestamp || item.time || item.arrival_date
    let timestamp;
    
    if (typeof rawTime === 'number') {
      const ms = rawTime < 1e12 ? rawTime * 1000 : rawTime
      timestamp = new Date(ms)
    } else if (typeof rawTime === 'string' && !rawTime.includes('Z') && !rawTime.includes('+')) {
      const isoTime = rawTime.includes(' ') ? rawTime.replace(' ', 'T') : rawTime;
      timestamp = new Date(isoTime + 'Z');
    } else {
      timestamp = new Date(rawTime);
    }

    if (isNaN(timestamp.getTime())) return // Skip invalid dates
    
    const val = item.avg !== undefined ? item.avg : (item.value !== undefined ? item.value : item.values?.[ch])
    
    channelGroups[ch].push({
      x: timestamp.getTime(),
      y: val !== undefined && val !== null ? Number(val) : null,
      min: item.min,
      max: item.max
    })
  })

  // Sort each group by timestamp
  Object.keys(channelGroups).forEach(ch => {
    channelGroups[ch].sort((a, b) => a.x - b.x)
  })
  
  return channelGroups
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
          adapters: {
            date: {
              locale: es
            }
          },
          time: {
            displayFormats: {
              minute: 'HH:mm',
              hour: 'HH:mm',
              day: 'MMM dd',
              month: 'MMM yyyy'
            }
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            maxRotation: 45,
            minRotation: 0
          }
        },
        y1: {
          type: 'linear',
          position: 'left',
          title: {
            display: true,
            text: capitalize(props.measurement1Type)
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.05)'
          }
        },
        y2: {
          type: 'linear',
          position: 'right',
          title: {
            display: true,
            text: capitalize(props.measurement2Type)
          },
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 15
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            title: (context) => {
              const date = new Date(context[0].parsed.x)
              return format(date, 'PPpp', { locale: es })
            },
            label: (context) => {
              const label = context.dataset.label || ''
              const value = context.parsed.y?.toFixed(2) || 'N/A'
              return `${label}: ${value}`
            }
          }
        }
      }
    }
  })
  
  // Fetch initial data
  fetchData()
})

// Watch for measurement type changes and refetch data
watch(() => [props.measurement1Type, props.measurement2Type, props.channel1, props.channel2], ([newM1, newM2, newCh1, newCh2], [oldM1, oldM2, oldCh1, oldCh2]) => {
  if ((newM1 && newM1 !== oldM1) || (newM2 && newM2 !== oldM2) || (newCh1 !== oldCh1) || (newCh2 !== oldCh2)) {
    console.log('🔄 Measurement types or channels changed, refetching data...')
    fetchData()
  }
})
</script>

<style scoped>
.combined-historical-chart-card {
  margin: 1rem 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  flex-wrap: wrap;
}

.title-section {
  flex: 1;
  min-width: 200px;
}

.filter-section {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.filter-section.is-mobile {
  flex-direction: column;
  align-items: stretch;
  width: 100%;
}

.date-filters, .other-filters {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.filter-section.is-mobile .date-filters,
.filter-section.is-mobile .other-filters {
  flex-direction: column;
  width: 100%;
}

.filter-item {
  display: flex;
  flex-direction: column;
}

.filter-item input,
.filter-item select {
  padding: 0.5rem;
  border: 1px solid var(--ion-color-light-shade);
  border-radius: 6px;
  font-size: 0.875rem;
}

.filter-section.is-mobile .filter-item input,
.filter-section.is-mobile .filter-item select {
  width: 100%;
}

ion-card-content {
  position: relative;
  min-height: 400px;
}

ion-card-content.is-mobile-content {
  min-height: 300px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
  gap: 1rem;
}

.loading-overlay p {
  color: var(--ion-color-medium);
  font-size: 0.875rem;
}

.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}

.is-mobile-content .chart-container {
  height: 300px;
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
  }
  
  .filter-section {
    width: 100%;
  }
}
</style>
