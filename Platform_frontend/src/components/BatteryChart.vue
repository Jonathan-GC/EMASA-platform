<template>
  <div class="battery-dashboard">
    <div class="header">
      <h1>Corriente IoT</h1>
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
        <p><strong>Muestras:</strong> {{ lastDevice.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Promedio:</strong> {{ (lastDevice.buffer_stats?.avg_value || 0).toFixed(2) }}V</p>
        <p><strong>Valor: </strong>{{ (lastDevice.buffer_stats?.max_voltage || 0).toFixed(1) }}V</p>
        </div>

      <div class="info-card">
        <h3>� Porcentaje de Batería</h3>
        <p><strong>Carga:</strong> {{ batteryPercentage || 0 }}%</p>
      </div>
 

      <div class="info-card">
        <h3>�📡 Radio</h3>
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

    <div class="chart-container" v-if="lastDevice">
      <Line
        :data="chartData"
        :options="chartOptions"
        :key="chartKey"
      />
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { Line } from 'vue-chartjs'
import { format } from 'date-fns'

// Cálculo del porcentaje de batería para batería de litio 12V
// Supongamos: 12.6V = 100%, 11.0V = 0%
const batteryPercentage = computed(() => {
  const maxV = lastDevice.value?.buffer_stats?.max_voltage || 0;
  const minV = 10.5; //según datos de saul
  const maxFull = 13.2; //según datos de saul
  if (maxV <= minV) return 0;
  if (maxV >= maxFull) return 100;
  const percent = ((maxV - minV) / (maxFull - minV)) * 100;
  return Math.round(percent);
});
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
  avg_value: number
  min_value: number
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

// Datos del gráfico
const chartData = reactive<ChartData<'line', ChartPoint[]>>({
  datasets: [
    {
      label: 'Batería (V)',
      data: [],
      borderColor: 'rgba(4, 116, 0, 1)',
      backgroundColor: 'rgba(4, 116, 0, 0.1)',
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 1,
      pointHoverRadius: 4,
      fill: false,
      yAxisID: 'y-left'
    },
    {
      label: 'Batería (%)',
      data: [],
      borderColor: 'rgba(116, 0, 87, 1)',
      backgroundColor: 'rgba(116, 0, 87, 0.1)',
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 1,
      pointHoverRadius: 4,
      fill: false,
      yAxisID: 'y-right'
    }
  ]
})

// Configuración del gráfico
const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    title: {
      display: true,
      text: `Mediciones de Batería - ${lastDevice.value?.device_name || 'Dispositivo IoT'}`
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
      //type: 'linear',
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
      //type: 'linear',
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
  
  // Solo procesar datos de corriente
  if (data.object?.type !== 'battery') {
    console.log(`ℹ️ Datos ignorados - tipo: ${data.object?.type}, esperando 'battery'`)
    return
  }
  
  // Actualizar información del dispositivo
  lastDevice.value = data
  
  // Agregar a mensajes recientes
  recentMessages.value.unshift(data)
  if (recentMessages.value.length > 10) {
    recentMessages.value.pop()
  }
  
  // Procesar valores de corriente para el gráfico
  const BatteryValues = data.object?.values || data.measurement_values
  if (BatteryValues && Array.isArray(BatteryValues)) {
    console.log(`📊 Procesando ${BatteryValues.length} muestras de voltaje`)
    
    const newPoints: ChartPoint[] = BatteryValues.map(sample => ({
      x: new Date(sample.time_iso),
      y: sample.value
    }))
    
    // Calcular puntos de porcentaje
    const percentagePoints: ChartPoint[] = BatteryValues.map(sample => {
      const voltage = sample.value;
      const minV = 10.5;
      const maxFull = 13.2;
      let percent = 0;
      if (voltage > minV) {
        if (voltage >= maxFull) {
          percent = 100;
        } else {
          percent = ((voltage - minV) / (maxFull - minV)) * 100;
        }
      }
      return {
        x: new Date(sample.time_iso),
        y: Math.round(percent)
      };
    });
    
    // Actualizar datos del gráfico
    chartData.datasets[0].data = newPoints
    chartData.datasets[1].data = percentagePoints
    
    // Forzar actualización del gráfico
    chartKey.value++
    
    console.log(`✅ Gráfico actualizado con ${newPoints.length} puntos`)
    console.log(`   Rango de tiempo: ${newPoints[0]?.x} - ${newPoints[newPoints.length - 1]?.x}`)
    console.log(`   Rango de batería: ${Math.min(...newPoints.map(p => p.y)).toFixed(3)}A - ${Math.max(...newPoints.map(p => p.y)).toFixed(3)}A`)
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
  console.log('🚀 Componente BatteryChart montado, iniciando conexión WebSocket...')
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
</style>
