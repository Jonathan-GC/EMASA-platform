<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>IoT Battery Monitor</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content :fullscreen="true">
      <div class="battery-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <h1>Batería IoT</h1>
          <div class="header-subtitle">
            <ConnectionStatus 
              :is-connected="isConnected" 
              :reconnect-attempts="reconnectAttempts" 
            />
          </div>
        </div>

        <!-- Device information section with battery details -->
        <BatteryDeviceInfo 
          :device="lastDevice" 
          :battery-percentage="batteryPercentage"
        />

        <!-- No data placeholder -->
        <div v-if="!lastDevice" class="no-data">
          <h2>🔍 Esperando datos del dispositivo...</h2>
          <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
          <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
        </div>

        <!-- Dual-axis battery chart -->
        <DualAxisBatteryChart 
          v-if="lastDevice && chartData.datasets[0].data.length > 0"
          :chart-data="chartData"
          :latest-data-points="latestDataPoints"
          :chart-key="chartKey"
          :device-name="lastDevice?.device_name || 'Dispositivo IoT'"
          :y-axis-min="BATTERY_MIN_V"
          :y-axis-max="BATTERY_MAX_V"
        />

        <!-- Recent messages -->
        <RecentMessages :messages="recentMessages" />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { onMounted } from 'vue'
import { 
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js'
import 'chartjs-adapter-date-fns'


// Import our composables
import { useWebSocket } from '@composables/useWebSocket.js'
import { useBatteryDataProcessor } from '@composables/useBatteryDataProcessor.js'

// Register Chart.js components
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

// Use our composables
const { isConnected, reconnectAttempts, setOnMessage } = useWebSocket()
const { 
  chartData, 
  latestDataPoints,
  lastDevice, 
  recentMessages, 
  chartKey, 
  batteryPercentage,
  processIncomingData 
} = useBatteryDataProcessor()

// Setup WebSocket message handler
onMounted(() => {
  setOnMessage(processIncomingData)
  console.log('🚀 Componente BatteryChart_C montado con arquitectura modular')
  console.log('🔋 Monitoreo de batería con doble eje (voltaje + porcentaje) iniciado')
})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.battery-dashboard {
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  margin: 0 0 15px 0;
  color: #374151;
  font-size: 2rem;
  font-weight: 600;
}

.header-subtitle {
  display: flex;
  justify-content: center;
  align-items: center;
}

.no-data {
  margin: 40px 0;
  text-align: center;
}

.no-data ion-card {
  max-width: 500px;
  margin: 0 auto;
}

.no-data h2 {
  color: #6b7280;
  margin: 0 0 10px 0;
}

.no-data p {
  color: #9ca3af;
  margin: 8px 0;
}

@media (max-width: 768px) {
  .battery-dashboard {
    padding: 15px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>