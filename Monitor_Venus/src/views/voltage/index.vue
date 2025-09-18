<template>
  <ion-page>
    <ion-header :translucent="true">
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/home"></ion-back-button>
        </ion-buttons>
        <ion-title>IoT Voltage Monitor</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content :fullscreen="true">
      <div class="multi-voltage-dashboard">
        <!-- Header with connection status -->
        <div class="header">
          <h1>Voltaje IoT - Múltiples Gráficas</h1>
          <div class="header-subtitle">
            <ConnectionStatus 
              :is-connected="isConnected" 
              :reconnect-attempts="reconnectAttempts" 
            />
          </div>
        </div>

        <!-- Device information section -->
        <DeviceInfo :device="lastDevice" />

        <!-- No data placeholder -->
        <div v-if="!lastDevice" class="no-data">
          <h2>🔍 Esperando datos del dispositivo...</h2>
          <p>Estado WebSocket: {{ isConnected ? 'Conectado' : 'Desconectado' }}</p>
          <p v-if="!isConnected">Intentando reconectar al WebSocket...</p>
        </div>

        <!-- Charts grid -->
        <ChartsGrid 
          :chart-fragments="chartDataFragments"
          :chart-key="chartKey"
          :device-name="lastDevice?.device_name || 'Dispositivo IoT'"
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

// Import our new focused components
/*import ConnectionStatus from './ConnectionStatus.vue'
import DeviceInfo from './DeviceInfo.vue'
import ChartsGrid from './ChartsGrid.vue'
import RecentMessages from './RecentMessages.vue'
*/
// Import our composables
import { useWebSocket } from '@composables/useWebSocket.js'
import { useVoltageDataProcessor } from '@composables/useVoltageDataProcessor.js'

/**
 * MultiVoltageChart Component - Main IoT dashboard
 * Responsibility: Orchestrate WebSocket connection and data display
 * 
 * This component now follows Single Responsibility Principle by:
 * - Delegating WebSocket management to useWebSocket composable
 * - Delegating data processing to useVoltageDataProcessor composable  
 * - Delegating UI sections to focused components
 */

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
  chartDataFragments, 
  lastDevice, 
  recentMessages, 
  chartKey, 
  processIncomingData 
} = useVoltageDataProcessor()

// Setup WebSocket message handler
onMounted(() => {
  setOnMessage(processIncomingData)
  console.log('🚀 Componente MultiVoltageChart montado con arquitectura modular')
})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.multi-voltage-dashboard {
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

/* Mobile responsiveness */
@media (max-width: 768px) {
  .multi-voltage-dashboard {
    padding: 15px;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
