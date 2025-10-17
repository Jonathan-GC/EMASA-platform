<template>
  <div class="device-info" v-if="device">
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📟 Dispositivo</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Nombre:</strong> {{ device.device_name || 'N/A' }}</p>
        <p><strong>DevEUI:</strong> {{ device.dev_eui || 'N/A' }}</p>
        <p><strong>Tenant:</strong> {{ device.tenant_id || 'N/A' }}</p>
      </ion-card-content>
    </ion-card>
    
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📊 Último Buffer</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Muestras:</strong> {{ device.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Promedio:</strong> {{ formatVoltage(device.buffer_stats?.avg_value || 0) }}V</p>
        <p><strong>Valor:</strong> {{ formatVoltage(device.buffer_stats?.max_voltage || 0) }}V</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card battery-card">
      <ion-card-header>
        <ion-card-title>🔋 Porcentaje de Batería <span v-if="channel">({{ channel }})</span></ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <div class="battery-level">
          <div class="battery-percentage" :class="getBatteryStatusClass()">
            {{ batteryPercentage || 0 }}%
          </div>
          <div class="battery-bar">
            <div 
              class="battery-fill" 
              :style="{ width: `${batteryPercentage || 0}%` }"
              :class="getBatteryStatusClass()"
            ></div>
          </div>
        </div>
        <p class="battery-status">
          <strong>Estado:</strong> {{ getBatteryStatusText() }}
        </p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Region:</strong> {{ device.region || 'N/A' }}dBm</p>
        <p><strong>SNR:</strong> {{ device.radio_info?.snr || 'N/A' }}dB</p>
        <p><strong>Frame:</strong> #{{ device.frame_counter || 0 }}</p>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
const props = defineProps({
  device: {
    type: Object,
    default: null
  },
  batteryPercentage: {
    type: Number,
    default: 0
  },
  channel: {
    type: String,
    default: ''
  }
})

const formatVoltage = (value) => {
  return (value || 0).toFixed(2)
}

const getBatteryStatusClass = () => {
  const percentage = props.batteryPercentage || 0
  if (percentage > 60) return 'battery-high'
  if (percentage > 30) return 'battery-medium'
  if (percentage > 15) return 'battery-low'
  return 'battery-critical'
}

const getBatteryStatusText = () => {
  const percentage = props.batteryPercentage || 0
  if (percentage > 60) return 'Buena'
  if (percentage > 30) return 'Media'
  if (percentage > 15) return 'Baja'
  return 'Crítica'
}
</script>

<style scoped>
.device-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.info-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.battery-card {
  border-left: 4px solid #4ade80;
}

.battery-level {
  text-align: center;
  margin: 15px 0;
}

.battery-percentage {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.battery-bar {
  width: 100%;
  height: 20px;
  background: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.battery-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
  border-radius: 10px;
}

.battery-high {
  color: #16a34a;
}

.battery-fill.battery-high {
  background: linear-gradient(90deg, #4ade80, #16a34a);
}

.battery-medium {
  color: #ca8a04;
}

.battery-fill.battery-medium {
  background: linear-gradient(90deg, #fbbf24, #ca8a04);
}

.battery-low {
  color: #ea580c;
}

.battery-fill.battery-low {
  background: linear-gradient(90deg, #fb923c, #ea580c);
}

.battery-critical {
  color: #dc2626;
}

.battery-fill.battery-critical {
  background: linear-gradient(90deg, #f87171, #dc2626);
}

@media (max-width: 768px) {
  .device-info {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .battery-percentage {
    font-size: 1.5rem;
  }
}
</style>