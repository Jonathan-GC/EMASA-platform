<template>
  <div class="multi-voltage-dashboard">
    <div class="header">
      <h1>Voltaje IoT - Múltiples Gráficas</h1>
      <div class="header-subtitle">
        <div class="connection-status" :class="{ connected: isConnected }">
          {{ isConnected ? '🟢 Conectado' : '🔴 Desconectado' }}
        </div>
      </div>
    </div>

    <div class="device-info" v-if="lastDevice">
      <div class="info-card">
        <h3>📟 Dispositivo</h3>
        <p><strong>Nombre:</strong> {{ lastDevice.device_name || 'N/A' }}</p>
        <p><strong>DevEUI:</strong> {{ lastDevice.dev_eui || 'N/A' }}</p>
        <p><strong>Tenant:</strong> {{ lastDevice.tenant_name || 'N/A' }}</p>
      </div>
      
      <div class="info-card">
        <h3>📊 Último Buffer</h3>
        <p><strong>Total Muestras:</strong> {{ lastDevice.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Fragmentos:</strong> {{ lastDevice.buffer_stats?.total_fragments || 0 }}</p>
        <p><strong>Promedio:</strong> {{ (lastDevice.buffer_stats?.avg_voltage || 0).toFixed(2) }}V</p>
        <p><strong>Rango:</strong> {{ (lastDevice.buffer_stats?.min_voltage || 0).toFixed(1) }}V - {{ (lastDevice.buffer_stats?.max_voltage || 0).toFixed(1) }}V</p>
      </div>

      <div class="info-card">
        <h3>📡 Radio</h3>
        <p><strong>RSSI:</strong> {{ lastDevice.radio_info?.rssi || 'N/A' }}dBm</p>
        <p><strong>SNR:</strong> {{ lastDevice.radio_info?.snr || 'N/A' }}dB</p>
        <p><strong>Frame:</strong> #{{ lastDevice.frame_counter || 0 }}</p>
      </div>
    </div>

    <div v-if="!lastDevice" class="no-data">
      <h2>🔍 Esperando datos del dispositivo...</h2>
      <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
      <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
    </div>

    <!-- Contenedor de múltiples gráficas -->
    <div 
      class="charts-grid" 
      v-if="lastDevice && chartDataFragments.length > 0"
      :style="{ '--grid-columns': gridColumns }"
    >
      <div 
        v-for="(fragment, index) in chartDataFragments" 
        :key="`chart-${index}-${chartKey}`"
        class="chart-fragment"
      >
        <h3>Sensor {{ index + 1 }} ({{ fragment.datasets[0].data.length }} muestras)</h3>
        <div class="chart-container">
          <Line
            :data="fragment"
            :options="getChartOptions(index + 1)"
          />
        </div>
      </div>
    </div>

    <div class="recent-messages" v-if="recentMessages.length > 0">
      <h3>📨 Mensajes Recientes</h3>
      <div class="message-list">
        <div 
          v-for="(message, index) in recentMessages" 
          :key="index"
          class="message-item"
        >
          <span class="timestamp">{{ formatTime(message.reception_timestamp) }}</span>
          <span class="device">{{ message.device_name }}</span>
          <span class="samples">{{ message.object?.values?.length || message.measurement_values?.length || 0 }} muestras</span>
          <span class="fragment">Frag: {{ message.object?.fragment_number || 'N/A' }}/{{ message.object?.total_fragments || 'N/A' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { Line } from 'vue-chartjs'
import { format } from 'date-fns'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  type ChartOptions,
  type ChartData
} from 'chart.js'
import 'chartjs-adapter-date-fns'

// Tipos TypeScript para los datos IoT
interface MeasurementValue {
  time: number
  time_iso: string
  value: number
}

interface BufferStats {
  total_samples: number
  avg_voltage: number
  min_voltage: number
  max_voltage: number
  measurement_type?: string
  series_id?: string
  fragment_number?: number
  total_fragments?: number
}

interface RadioInfo {
  rssi: number
  snr: number
  frequency?: number
  gateway_id?: string
}

interface DeviceData {
  device_name: string
  dev_eui: string
  tenant_name: string
  tenant_id?: string
  application_name?: string
  buffer_stats?: BufferStats
  radio_info?: RadioInfo
  frame_counter: number
  measurement_values?: MeasurementValue[]
  reception_timestamp: string
  message_time?: string
  dev_address?: string
  error?: string
  object?: {
    type: string
    measurement?: string
    values?: MeasurementValue[]
    series_id?: number
    message_arrival_time?: number
    fragment_number?: number
    total_fragments?: number
  }
}

interface ChartPoint {
  x: Date
  y: number
}

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
)

// Estado reactivo
const isConnected = ref<boolean>(false)
const websocket = ref<WebSocket | null>(null)
const lastDevice = ref<DeviceData | null>(null)
const recentMessages = ref<DeviceData[]>([])
const chartKey = ref<number>(0)
const reconnectAttempts = ref<number>(0)

// Datos de múltiples gráficas - cada elemento representa un fragmento de 50 muestras
const chartDataFragments = ref<ChartData<'line', ChartPoint[]>[]>([])

// Computed property para calcular el número de columnas dinámicamente
const gridColumns = computed(() => {
  const numFragments = chartDataFragments.value.length
  // Máximo de 3 columnas por fila como solicita el usuario
  return Math.min(numFragments, 3)
})

// Función para crear datos de gráfica para un fragmento
const createChartData = (points: ChartPoint[], fragmentIndex: number): ChartData<'line', ChartPoint[]> => {
  const colors = [
    'rgb(59, 130, 246)',   // Azul
    'rgba(246, 59, 59, 1)',   // Verde
    'rgba(4, 116, 0, 1)'   // Rojo
  ]
  
  const color = colors[fragmentIndex % colors.length]
  
  return {
    datasets: [{
      label: `Voltaje Fragmento ${fragmentIndex + 1} (V)`,
      data: points,
      borderColor: color,
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 1,
      pointHoverRadius: 4,
      fill: false
    }]
  }
}

// Configuración del gráfico para cada fragmento
const getChartOptions = (fragmentNumber: number): ChartOptions<'line'> => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    title: {
      display: true,
      text: `Fragmento ${fragmentNumber} - ${lastDevice.value?.device_name || 'Dispositivo IoT'}`
    },
    legend: {
      display: true
    },
    tooltip: {
      callbacks: {
        title: function(context: any[]) {
          if (context[0]?.parsed?.x) {
            return format(new Date(context[0].parsed.x), 'HH:mm:ss.SSS')
          }
          return ''
        },
        label: function(context: any) {
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
})

// Funciones
const connectWebSocket = (): void => {
  console.log('🔄 Intentando conectar al WebSocket...')

  const wsURL = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8765'
  
  try {
    websocket.value = new WebSocket(wsURL)
    
    websocket.value.onopen = () => {
      isConnected.value = true
      reconnectAttempts.value = 0
      console.log('🟢 Conectado al WebSocket exitosamente')
    }
    
    websocket.value.onmessage = (event: MessageEvent) => {
      try {
        const data: DeviceData = JSON.parse(event.data)
        console.log('📥 Datos recibidos del WebSocket:', data)
        processIncomingData(data)
      } catch (error) {
        console.error('❌ Error procesando mensaje del WebSocket:', error)
        setTimeout(connectWebSocket, 5000) // Reintentar conexión
      }
    }
    
    websocket.value.onclose = () => {
      isConnected.value = false
      reconnectAttempts.value++
      console.log(`🔴 WebSocket desconectado. Intento de reconexión #${reconnectAttempts.value}`)
      
      // Reconectar con backoff exponencial
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
      setTimeout(connectWebSocket, delay)
    }
    
    websocket.value.onerror = (error: Event) => {
      console.error('❌ Error en WebSocket:', error)
    }
    
  } catch (error) {
    console.error('❌ Error creando WebSocket:', error)
    setTimeout(connectWebSocket, 5000)
  }
}

const processIncomingData = (data: DeviceData): void => {
  // Verificar si hay error en los datos
  if (data.error) {
    console.warn('⚠️ Datos con error recibidos:', data.error)
    return
  }
  
  // Solo procesar datos de voltaje
  if (data.object?.type !== 'voltage') {
    console.log(`ℹ️ Datos ignorados - tipo: ${data.object?.type}, esperando 'voltage'`)
    return
  }
  
  // Actualizar información del dispositivo
  lastDevice.value = data
  
  // Agregar a mensajes recientes
  recentMessages.value.unshift(data)
  if (recentMessages.value.length > 10) {
    recentMessages.value.pop()
  }
  
  // Procesar valores de voltaje para el gráfico
  const voltageValues = data.object?.values || data.measurement_values
  if (voltageValues && Array.isArray(voltageValues)) {
    console.log(`📊 Procesando ${voltageValues.length} muestras de voltaje`)
    
    // Convertir todas las muestras a puntos del gráfico
    const allPoints: ChartPoint[] = voltageValues.map(sample => ({
      x: new Date(sample.time_iso),
      y: sample.value
    }))
    
    // Dividir en fragmentos de 50 muestras
    const fragmentSize = 50
    const fragments: ChartPoint[][] = []
    
    for (let i = 0; i < allPoints.length; i += fragmentSize) {
      const fragment = allPoints.slice(i, i + fragmentSize)
      fragments.push(fragment)
    }
    
    // Crear datos de gráfica para cada fragmento
    chartDataFragments.value = fragments.map((fragment, index) => 
      createChartData(fragment, index)
    )
    
    // Forzar actualización del gráfico
    chartKey.value++
    
    console.log(`✅ Gráficos actualizados con ${fragments.length} fragmentos`)
    fragments.forEach((fragment, index) => {
      console.log(`   Fragmento ${index + 1}: ${fragment.length} puntos`)
      if (fragment.length > 0) {
        console.log(`     Tiempo: ${fragment[0]?.x} - ${fragment[fragment.length - 1]?.x}`)
        console.log(`     Voltaje: ${Math.min(...fragment.map(p => p.y)).toFixed(3)}V - ${Math.max(...fragment.map(p => p.y)).toFixed(3)}V`)
      }
    })
  } else {
    console.log('ℹ️ No hay valores de medición en los datos recibidos')
  }
}

const formatTime = (timestamp: string): string => {
  try {
    return format(new Date(timestamp), 'HH:mm:ss')
  } catch {
    return 'N/A'
  }
}

// Ciclo de vida
onMounted(() => {
  console.log('🚀 Componente MultiVoltageChart montado, iniciando conexión WebSocket...')
  connectWebSocket()
})

onUnmounted(() => {
  console.log('🛑 Componente desmontado, cerrando WebSocket...')
  if (websocket.value) {
    websocket.value.close()
  }
})
</script>

<style scoped>
@import '../assets/css/dashboard.css';

.multi-voltage-dashboard {
  padding: 20px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns, 1), 1fr);
  gap: 30px;
  margin-top: 20px;
}

.chart-fragment {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-fragment h3 {
  margin: 0 0 15px 0;
  color: #374151;
  font-size: 1.1em;
  font-weight: 600;
}

.chart-container {
  height: 300px;
  position: relative;
}

.message-item .fragment {
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  margin-left: 8px;
}

/* Responsive design para múltiples gráficas */
/* Mobile: Always 1 column */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr !important;
  }
}

/* Tablet: Maximum 2 columns */
@media (min-width: 769px) and (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: repeat(min(var(--grid-columns, 1), 2), 1fr) !important;
  }
}

/* Desktop: Maximum 3 columns as requested */
@media (min-width: 1025px) {
  .charts-grid {
    grid-template-columns: repeat(min(var(--grid-columns, 1), 3), 1fr);
  }
}
</style>
