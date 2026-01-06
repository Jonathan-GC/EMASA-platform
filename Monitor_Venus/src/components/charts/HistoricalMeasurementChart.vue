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
              <input type="datetime-local" v-model="filters.start" :max="today" :min="yesterday" @change="fetchData" />
            </div>
            <div class="filter-item">
              <input type="datetime-local" v-model="filters.end" :max="today" :min="yesterday" @change="fetchData"  />
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
      </div>
      <div class="chart-container">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>

  <!-- Detailed Points Table -->
  <ion-card v-if="showDetailedTable" class="detailed-points-table">
    <ion-card-header>
      <div class="table-header">
        <ion-card-title>📊 Datos Detallados</ion-card-title>
        <ion-button size="small" fill="clear" @click="closeDetailedTable">
          ✕
        </ion-button>
      </div>
      <ion-card-subtitle>
        {{ detailedPointsInfo }}
      </ion-card-subtitle>
    </ion-card-header>
    <ion-card-content>
      <div v-if="loadingDetails" class="loading-details">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando datos detallados...</p>
      </div>
      <div v-else-if="detailedTableData.length > 0" class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Hora</th>
              <th>Canal</th>
              <th>Valor</th>
              <th>Dispositivo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedTableData" :key="idx">
              <td>{{ row.time }}</td>
              <td>{{ row.channel }}</td>
              <td>{{ row.value }}</td>
              <td>{{ row.device }}</td>
            </tr>
          </tbody>
        </table>
        
        <!-- Pagination -->
        <div class="pagination" v-if="detailedTableData.length > 0">
          <div class="pagination-left">
            <span class="pagination-label">Items per page:</span>
            <select v-model.number="itemsPerPage" class="items-per-page-select">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="pagination-center">
            <span class="page-range">
              {{ (currentPage - 1) * itemsPerPage + 1 }}-{{ Math.min(currentPage * itemsPerPage, detailedTableData.length) }} of {{ detailedTableData.length }}
            </span>
          </div>
          <div class="pagination-right">
            <ion-button 
              size="small" 
              fill="clear" 
              :disabled="currentPage === 1"
              @click="currentPage = 1"
            >
              |‹
            </ion-button>
            <ion-button 
              size="small" 
              fill="clear" 
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              ‹
            </ion-button>
            <ion-button 
              size="small" 
              fill="clear" 
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              ›
            </ion-button>
            <ion-button 
              size="small" 
              fill="clear" 
              :disabled="currentPage === totalPages"
              @click="currentPage = totalPages"
            >
              ›|
            </ion-button>
          </div>
        </div>
      </div>
      <div v-else class="no-data">
        <p>No hay datos detallados disponibles para este punto.</p>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { ref, onMounted, watch, reactive, computed } from 'vue'
import { 
  IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, 
  IonCardContent, IonSpinner, IonButton 
} from '@ionic/vue'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'
import API from '@/utils/api/api.js'
import { format, subDays } from 'date-fns'
import { es } from 'date-fns/locale'
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
const today = format(new Date(), "yyyy-MM-dd'T'HH:mm")
const yesterday = format(subDays(new Date(), 89), "yyyy-MM-dd'T'HH:mm")

// Detailed points table state
const showDetailedTable = ref(false)
const loadingDetails = ref(false)
const detailedTableData = ref([])
const detailedPointsInfo = ref('')
const currentPage = ref(1)
const itemsPerPage = 10

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
  start: format(subDays(new Date(), 89), "yyyy-MM-dd'T'HH:mm"),
  end: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  measurement_type: props.initialType,
  step: 100
})

// Watch for initialType changes to update the chart automatically
watch(() => props.initialType, (newType) => {
  if (newType) {
    filters.measurement_type = newType
    fetchData()
  }
})

const stepValue = computed({
  get: () => filters.step,
  set: (val) => {
    filters.step = Math.min(Math.max(1, val), 300)
  }
})

const capitalize = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : ''

// Computed properties for pagination
const totalPages = computed(() => Math.ceil(detailedTableData.value.length / itemsPerPage))

const paginatedTableData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return detailedTableData.value.slice(start, end)
})

const closeDetailedTable = () => {
  showDetailedTable.value = false
  detailedTableData.value = []
  currentPage.value = 1
}

// Fetch detailed points from API
const fetchDetailedPoints = async (clickedPoint, prevPoint, nextPoint) => {
  if (!clickedPoint || !props.deviceId) return
  
  loadingDetails.value = true
  showDetailedTable.value = true
  detailedTableData.value = []
  
  try {
    // Calculate time window using previous and next point timestamps
    const pointTimestamp = clickedPoint.x
    
    // Use previous point's timestamp as start, or current point - 1 second if first point
    const startTimestamp = prevPoint ? prevPoint.x : pointTimestamp - 1000
    
    // Use next point's timestamp as end, or current point + 1 second if last point
    const endTimestamp = nextPoint ? nextPoint.x : pointTimestamp + 1000
    
    const start = new Date(startTimestamp).toISOString()
    const end = new Date(endTimestamp).toISOString()
    
    console.log('🕐 Time window:', {
      start: format(new Date(startTimestamp), 'HH:mm:ss.SSS'),
      clicked: format(new Date(pointTimestamp), 'HH:mm:ss.SSS'),
      end: format(new Date(endTimestamp), 'HH:mm:ss.SSS')
    })
    
    const params = new URLSearchParams({
      start,
      end,
      measurement_type: filters.measurement_type
    })
    
    const url = `${API.DETAILED_POINTS(props.deviceId)}?${params.toString()}`
    console.log('📡 Fetching detailed points:', url)
    
    const response = await API.get(url)
    const data = Array.isArray(response) ? response : (response.data || [])
    
    // Parse the nested structure and flatten for table display
    const tableRows = []
    
    data.forEach(item => {
      const deviceName = item.device_name || 'Unknown'
      const measurements = item.payload?.measurements?.[filters.measurement_type]
      
      if (measurements) {
        // Iterate through channels
        Object.entries(measurements).forEach(([channel, samples]) => {
          if (Array.isArray(samples)) {
            samples.forEach(sample => {
              // Use client-side time from sample, not server timestamp
              const sampleTime = sample.time || item.payload?.arrival_date || item.timestamp
              tableRows.push({
                time: format(new Date(sampleTime), 'HH:mm:ss', { locale: es }),
                channel: channel,
                value: sample.value?.toFixed(2) || 'N/A',
                device: deviceName
              })
            })
          }
        })
      }
    })
    
    // Sort by time
    tableRows.sort((a, b) => a.time.localeCompare(b.time))
    
    detailedTableData.value = tableRows
    detailedPointsInfo.value = `${tableRows.length} muestras encontradas cerca de ${format(new Date(pointTimestamp), 'HH:mm:ss', { locale: es })}`
    
    console.log('✅ Detailed points loaded:', tableRows.length, 'samples')
  } catch (error) {
    console.error('❌ Error fetching detailed points:', error)
    detailedPointsInfo.value = 'Error al cargar datos detallados'
  } finally {
    loadingDetails.value = false
  }
}

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
    subtitle.value = `Datos desde ${format(new Date(filters.start), 'MMM dd', { locale: es })} hasta ${format(new Date(filters.end), 'MMM dd', { locale: es })}`
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
      
      let rawTime = item.timestamp || item.time || item.arrival_date
      let timestamp;
      
      if (typeof rawTime === 'number') {
        const ms = rawTime < 1e12 ? rawTime * 1000 : rawTime
        timestamp = new Date(ms)
      } else if (typeof rawTime === 'string' && !rawTime.includes('Z') && !rawTime.includes('+')) {
        // If the string doesn't have timezone info, assume it's UTC and add 'Z'
        // This ensures the browser converts it to local time correctly
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
      onClick: (event, activeElements) => {
        if (activeElements && activeElements.length > 0) {
          const firstElement = activeElements[0]
          const datasetIndex = firstElement.datasetIndex
          const index = firstElement.index
          const dataset = chartInstance.data.datasets[datasetIndex]
          const clickedPoint = dataset.data[index]
          
          // Get previous and next points for time window
          const prevPoint = index > 0 ? dataset.data[index - 1] : null
          const nextPoint = index < dataset.data.length - 1 ? dataset.data[index + 1] : null
          
          console.log('📍 Point clicked:', clickedPoint)
          fetchDetailedPoints(clickedPoint, prevPoint, nextPoint)
        }
      },
      onHover: (event, activeElements) => {
        event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
      },
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
            display: true,
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

            drawBorder: false,
            display: true
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
              return format(new Date(context[0].parsed.x), 'MMM dd, HH:mm', { locale: es })
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

/* Detailed Points Table Styles */
.detailed-points-table {
  margin-top: 20px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-details {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--ion-color-medium);
}

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.data-table thead {
  background: var(--ion-color-light);
  position: sticky;
  top: 0;
  z-index: 1;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--ion-color-dark);
  border-bottom: 2px solid var(--ion-color-medium);
}

.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--ion-color-light-shade);
  color: var(--ion-text-color);
}

.data-table tbody tr:hover {
  background: var(--ion-color-light);
}

.data-table tbody tr:nth-child(even) {
  background: rgba(var(--ion-color-light-rgb), 0.3);
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 12px 16px;
  border-top: 1px solid var(--ion-color-light-shade);
  gap: 16px;
}

.pagination-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination-label {
  font-size: 0.875rem;
  color: var(--ion-color-medium);
  font-weight: 500;
}

.items-per-page-select {
  background: var(--ion-background-color, transparent);
  border: 1px solid var(--ion-border-color, rgba(255, 255, 255, 0.1));
  border-radius: 6px;
  padding: 6px 32px 6px 12px;
  font-size: 0.875rem;
  color: var(--ion-text-color);
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239ca3af' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 12px;
  transition: all 0.2s;
}

.items-per-page-select:hover {
  border-color: var(--ion-color-primary);
}

.items-per-page-select:focus {
  border-color: var(--ion-color-primary);
  background-color: rgba(var(--ion-color-primary-rgb), 0.05);
}

.pagination-center {
  flex: 1;
  text-align: center;
}

.page-range {
  font-size: 0.875rem;
  color: var(--ion-color-medium);
  font-weight: 500;
}

.pagination-right {
  display: flex;
  gap: 4px;
}

.pagination-right ion-button {
  min-width: 36px;
  height: 36px;
  --padding-start: 8px;
  --padding-end: 8px;
}

.page-info {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  font-weight: 500;
}

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: var(--ion-color-medium);
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
