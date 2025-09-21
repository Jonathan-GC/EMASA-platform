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

        <!-- Device information section with battery details for each channel -->
        <template v-if="lastDevice && Object.keys(channelChartData).length > 0">
          <div v-for="(data, channel, idx) in channelChartData" :key="channel">
            <BatteryDeviceInfo
              :device="lastDevice"
              :battery-percentage="data.percentage.length > 0 ? data.percentage[data.percentage.length - 1].y : 0"
              :channel="channel"
            />
            <DualAxisBatteryChart
              :chart-data="{ datasets: [
                { label: `Batería (V) ${channel}`, data: data.voltage, borderColor: 'rgba(4, 116, 0, 1)', backgroundColor: 'rgba(4, 116, 0, 0.1)', borderWidth: 2, tension: 0.1, pointRadius: 1, pointHoverRadius: 4, fill: false, yAxisID: 'y-left' },
                { label: `Batería (%) ${channel}`, data: data.percentage, borderColor: 'rgba(116, 0, 87, 1)', backgroundColor: 'rgba(116, 0, 87, 0.1)', borderWidth: 2, tension: 0.1, pointRadius: 1, pointHoverRadius: 4, fill: false, yAxisID: 'y-right' }
              ] }"
              :chart-key="chartKey + idx"
              :device-name="lastDevice?.device_name || 'Dispositivo IoT' + ' ' + channel"
            />
          </div>
        </template>

        <!-- No data placeholder -->
        <div v-if="!lastDevice" class="no-data">
          <h2>🔍 Esperando datos del dispositivo...</h2>
          <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
          <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
        </div>

        <!-- Recent messages -->
        <RecentMessages :messages="recentMessages" />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
import DualAxisBatteryChart from '@/components/charts/DualAxisBatteryChart.vue'
import BatteryDeviceInfo from '@/components/BatteryDeviceInfo.vue'
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import RecentMessages from '@/components/RecentMessages.vue'

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
  channelChartData,
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