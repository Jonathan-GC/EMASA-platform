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
            <ion-button size="small" fill="outline" @click="exportPDF" :disabled="loading || exportingPDF" class="export-button">
              <ion-icon slot="start" :icon="exportingPDF ? '' : (icons.download || icons.save)"></ion-icon>
              <ion-spinner v-if="exportingPDF" name="crescent" size="small"></ion-spinner>
              <span v-else>PDF</span>
            </ion-button>
          </div>
        </div>
      </div>
    </ion-card-header>

    <ion-card-content :class="{ 'is-mobile-content': isMobile }">
      <div v-if="loading" class="loading-overlay">
        <ion-spinner name="crescent"></ion-spinner>
        <p>Cargando datos...</p>
      </div>
      
      <div v-else-if="rawHistoricalData.data1.length === 0 && rawHistoricalData.data2.length === 0" class="no-data-overlay">
        <ion-icon :icon="icons.analytics" size="large" color="medium"></ion-icon>
        <p>No hay datos históricos para el periodo seleccionado</p>
        <small>Intenta ampliar el rango de fechas o aumentar los pasos.</small>
      </div>

      <div class="chart-container" v-show="!loading && (rawHistoricalData.data1.length > 0 || rawHistoricalData.data2.length > 0)">
        <canvas ref="canvasRef"></canvas>
      </div>
    </ion-card-content>
  </ion-card>

  <!-- Detailed Points Table -->
  <ion-card v-if="showDetailedTable" class="detailed-points-table">
    <ion-card-header>
      <div class="table-header">
        <ion-card-title>
          <ion-icon :icon="icons.bar_chart" size="small"class="ms-2"></ion-icon>
          Datos Detallados</ion-card-title>
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
              <th>Medición</th>
              <th>Canal</th>
              <th>Valor</th>
              <th>Dispositivo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedTableData" :key="idx">
              <td>{{ row.time }}</td>
              <td>{{ row.measurement }}</td>
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
import { ref, onMounted, reactive, computed, watch, inject } from 'vue'
import { IonCard, IonCardHeader, IonCardTitle, IonCardSubtitle, IonCardContent, IonSpinner, IonButton, IonIcon } from '@ionic/vue'
import { Chart, registerables } from 'chart.js'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'
import API from '@/utils/api/api.js'
import { format, subDays } from 'date-fns'
import { es } from 'date-fns/locale'
import { useResponsiveView } from '@/composables/useResponsiveView.js'
import { jsPDF } from 'jspdf'
import autoTable from 'jspdf-autotable'
import logoImage from '@/assets/monitor_logo.png'

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
  availableMeasurements: {
    type: Array,
    default: () => []
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
const icons = inject('icons')

const loading = ref(false)
const title = ref('Comparación de Mediciones')
const subtitle = ref('Últimos datos históricos')
const today = format(new Date(), "yyyy-MM-dd'T'HH:mm")
const yesterday = format(subDays(new Date(), 89), "yyyy-MM-dd'T'HH:mm")

// Export state
const exportingPDF = ref(false)
const rawHistoricalData = ref({ data1: [], data2: [] })

// Detailed points table state
const showDetailedTable = ref(false)
const loadingDetails = ref(false)
const detailedTableData = ref([])
const detailedPointsInfo = ref('')
const currentPage = ref(1)
const itemsPerPage = ref(10)
const clickedPointX = ref(null)

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

// Computed properties for pagination
const totalPages = computed(() => Math.ceil(detailedTableData.value.length / itemsPerPage.value))

const paginatedTableData = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return detailedTableData.value.slice(start, end)
})

const closeDetailedTable = () => {
  showDetailedTable.value = false
  detailedTableData.value = []
  currentPage.value = 1
  clickedPointX.value = null
  
  // Hide the vertical line
  if (chartInstance && chartInstance.options.plugins.annotation) {
    chartInstance.options.plugins.annotation.annotations.clickLine.display = false
    chartInstance.update('none')
  }
}

const exportPDF = async () => {
  if (!chartInstance || exportingPDF.value) return
  
  exportingPDF.value = true
  try {
    const doc = new jsPDF({
      orientation: 'landscape',
      unit: 'mm',
      format: 'a4'
    })
    
    const timestamp = format(new Date(), 'yyyyMMdd_HHmm')
    const fileName = `Reporte_${props.deviceId}_${timestamp}.pdf`
    
    // Get threshold info for both measurements
    const m1Info = props.availableMeasurements.find(m => m.unit?.toLowerCase() === props.measurement1Type?.toLowerCase())
    const m2Info = props.availableMeasurements.find(m => m.unit?.toLowerCase() === props.measurement2Type?.toLowerCase())

    // 1. Header with Logo
    try {
      doc.addImage(logoImage, 'PNG', doc.internal.pageSize.getWidth() - 45, 10, 30, 9)
    } catch (e) {
      console.warn('Logo not loaded:', e)
    }
    
    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(33, 33, 33)
    doc.text(title.value, 50, 20)
    
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(100, 100, 100)
    doc.text(subtitle.value, 50, 28)
    doc.text(`Dispositivo: ${props.deviceId} | Generado: ${format(new Date(), 'PPpp', { locale: es })}`, 15, 34)
    
    // 2. Chart
    const chartImage = chartInstance.toBase64Image('png', 1)
    const imgWidth = 260
    const imgHeight = (chartInstance.height * imgWidth) / chartInstance.width
    doc.addImage(chartImage, 'PNG', 15, 40, imgWidth, imgHeight)
    
    // 3. Table - Prioritize detailedTableData if it exists, otherwise use rawHistoricalData
    let exportData = []
    let tableHeaders = []
    
    if (detailedTableData.value && detailedTableData.value.length > 0) {
      exportData = detailedTableData.value.map(row => [
        row.time,
        row.measurement,
        row.channel,
        row.value,
        row.device
      ])
      tableHeaders = [['Hora', 'Medición', 'Canal', 'Valor', 'Dispositivo']]
    } else {
      // Build from historical data (less points but covers whole range)
      const { data1, data2 } = rawHistoricalData.value
      
      const processItem = (item, type) => {
        let rawTime = item.timestamp || item.time || item.arrival_date
        let timeStr = ''
        try {
          const ms = typeof rawTime === 'number' ? (rawTime < 1e12 ? rawTime * 1000 : rawTime) : new Date(rawTime).getTime()
          timeStr = format(new Date(ms), 'MMM dd, HH:mm:ss', { locale: es })
        } catch (e) { timeStr = 'N/A' }
        
        return [
          timeStr,
          capitalize(type),
          item.channel || 'default',
          item.avg?.toFixed(2) || item.value?.toFixed(2) || 'N/A',
          item.device_name || 'N/A'
        ]
      }
      
      const rows1 = data1.map(item => processItem(item, props.measurement1Type))
      const rows2 = data2.map(item => processItem(item, props.measurement2Type))
      
      exportData = [...rows1, ...rows2].sort((a, b) => a[0].localeCompare(b[0]))
      tableHeaders = [['Hora', 'Medición', 'Canal', 'Valor', 'Dispositivo']]
    }
    
    if (exportData.length > 0) {
      autoTable(doc, {
        startY: imgHeight + 50,
        head: tableHeaders,
        body: exportData,
        theme: 'striped',
        headStyles: { 
          fillColor: [45, 45, 45],
          textColor: [255, 255, 255],
          fontStyle: 'bold'
        },
        styles: { fontSize: 8 },
        margin: { top: 20 },
        didParseCell: (data) => {
          if (data.section === 'body' && data.column.index === 3) {
            const mType = data.row.cells[1].raw?.toString().toLowerCase()
            const val = parseFloat(data.cell.raw)
            
            const info = (mType === props.measurement1Type?.toLowerCase()) ? m1Info : 
                         (mType === props.measurement2Type?.toLowerCase()) ? m2Info : null
            
            if (info && !isNaN(val) && info.min !== undefined && info.max !== undefined && info.threshold !== undefined) {
              if (val < info.min || val > info.max) {
                Object.values(data.row.cells).forEach(cell => {
                  cell.styles.fillColor = [255, 230, 230]
                  cell.styles.textColor = [120, 20, 20]
                })
              } else if ((val >= info.min && val < info.min + info.threshold) || (val <= info.max && val > info.max - info.threshold)) {
                Object.values(data.row.cells).forEach(cell => {
                  cell.styles.fillColor = [255, 245, 220]
                  cell.styles.textColor = [150, 90, 10]
                })
              }
            }
          }
        },
        didDrawPage: (data) => {
          doc.setFontSize(8)
          doc.text(`Página ${data.pageNumber}`, doc.internal.pageSize.width - 25, doc.internal.pageSize.height - 10)
        }
      })
    }
    
    doc.save(fileName)
    console.log('✅ PDF Exported successfully')
  } catch (error) {
    console.error('❌ Error exporting PDF:', error)
  } finally {
    exportingPDF.value = false
  }
}

// Fetch detailed points from API for both measurements
const fetchDetailedPoints = async (clickedPoint, prevPoint, nextPoint, datasetIndex) => {
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
    
    // Fetch data for BOTH measurements
    const params1 = new URLSearchParams({
      start,
      end,
      measurement_type: props.measurement1Type
    })
    
    const params2 = new URLSearchParams({
      start,
      end,
      measurement_type: props.measurement2Type
    })
    
    const url1 = `${API.DETAILED_POINTS(props.deviceId)}?${params1.toString()}`
    const url2 = `${API.DETAILED_POINTS(props.deviceId)}?${params2.toString()}`
    
    console.log('📡 Fetching detailed points for both:', props.measurement1Type, 'and', props.measurement2Type)
    
    // Fetch both measurements in parallel
    const [response1, response2] = await Promise.all([
      API.get(url1),
      API.get(url2)
    ])
    
    const data1 = Array.isArray(response1) ? response1 : (response1.data || [])
    const data2 = Array.isArray(response2) ? response2 : (response2.data || [])
    
    // Parse the nested structure and flatten for table display
    const tableRows = []
    
    // Process measurement 1 data
    data1.forEach(item => {
      const deviceName = item.device_name || 'Unknown'
      const measurements = item.payload?.measurements?.[props.measurement1Type]
      
      if (measurements) {
        // Iterate through channels
        Object.entries(measurements).forEach(([channel, samples]) => {
          // If channel filter is specified for measurement 1, only include that channel
          if (props.channel1 && channel !== `ch${props.channel1}`) {
            return // Skip this channel
          }
          
          if (Array.isArray(samples)) {
            samples.forEach(sample => {
              // Use client-side time from sample, not server timestamp
              const sampleTime = sample.time || item.payload?.arrival_date || item.timestamp
              tableRows.push({
                time: format(new Date(sampleTime), 'HH:mm:ss', { locale: es }),
                measurement: capitalize(props.measurement1Type),
                channel: channel,
                value: sample.value?.toFixed(2) || 'N/A',
                device: deviceName
              })
            })
          }
        })
      }
    })
    
    // Process measurement 2 data
    data2.forEach(item => {
      const deviceName = item.device_name || 'Unknown'
      const measurements = item.payload?.measurements?.[props.measurement2Type]
      
      if (measurements) {
        // Iterate through channels
        Object.entries(measurements).forEach(([channel, samples]) => {
          // If channel filter is specified for measurement 2, only include that channel
          if (props.channel2 && channel !== `ch${props.channel2}`) {
            return // Skip this channel
          }
          
          if (Array.isArray(samples)) {
            samples.forEach(sample => {
              // Use client-side time from sample, not server timestamp
              const sampleTime = sample.time || item.payload?.arrival_date || item.timestamp
              tableRows.push({
                time: format(new Date(sampleTime), 'HH:mm:ss', { locale: es }),
                measurement: capitalize(props.measurement2Type),
                channel: channel,
                value: sample.value?.toFixed(2) || 'N/A',
                device: deviceName
              })
            })
          }
        })
      }
    })
    
    // Sort by time, then by measurement, then by channel
    tableRows.sort((a, b) => {
      const timeCompare = a.time.localeCompare(b.time)
      if (timeCompare !== 0) return timeCompare
      
      const measurementCompare = a.measurement.localeCompare(b.measurement)
      if (measurementCompare !== 0) return measurementCompare
      
      return a.channel.localeCompare(b.channel)
    })
    
    detailedTableData.value = tableRows
    
    // Build info text based on filters
    const measurement1Label = `${capitalize(props.measurement1Type)}${props.channel1 ? ` (${props.channel1})` : ''}`
    const measurement2Label = `${capitalize(props.measurement2Type)}${props.channel2 ? ` (${props.channel2})` : ''}`
    detailedPointsInfo.value = `${tableRows.length} muestras encontradas cerca de ${format(new Date(pointTimestamp), 'HH:mm:ss', { locale: es })} para ${measurement1Label} y ${measurement2Label}`
    
    console.log('✅ Detailed points loaded:', tableRows.length, 'samples from both measurements')
  } catch (error) {
    console.error('❌ Error fetching detailed points:', error)
    detailedPointsInfo.value = 'Error al cargar datos detallados'
  } finally {
    loadingDetails.value = false
  }
}

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
    
    rawHistoricalData.value = { data1, data2 }
    
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
    // Blue, Violet, Emerald
    const colors1 = ['#3b82f6', '#8b5cf6', '#10b981']
    
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
    // Amber, Pink, Indigo
    const colors2 = ['#f59e0b', '#ec4899', '#6366f1']
    
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
          
          // Store clicked point x position and update annotation
          clickedPointX.value = clickedPoint.x
          if (chartInstance.options.plugins.annotation) {
            chartInstance.options.plugins.annotation.annotations.clickLine.xMin = clickedPoint.x
            chartInstance.options.plugins.annotation.annotations.clickLine.xMax = clickedPoint.x
            chartInstance.options.plugins.annotation.annotations.clickLine.display = true
            chartInstance.update('none')
          }
          
          console.log('📍 Point clicked:', clickedPoint)
          fetchDetailedPoints(clickedPoint, prevPoint, nextPoint, datasetIndex)
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
        annotation: {
          annotations: {
            clickLine: {
              type: 'line',
              xMin: 0,
              xMax: 0,
              borderColor: 'rgba(0, 0, 0, 0.8)',
              borderWidth: 2,
              display: false,
              label: {
                display: false
              }
            }
          }
        },
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

.export-button {
  margin-left: 8px;
  font-weight: 600;
  --border-radius: 8px;
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

.no-data-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 350px;
  text-align: center;
  color: var(--ion-color-medium);
  gap: 0.5rem;
}

.no-data-overlay p {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
  color: var(--ion-color-step-600);
}

.no-data-overlay small {
  font-size: 0.85rem;
  opacity: 0.7;
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

.no-data {
  text-align: center;
  padding: 40px 20px;
  color: var(--ion-color-medium);
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
