<template>
  <div class="device-info" v-if="device">
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📟 Dispositivo</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Nombre:</strong> {{ device.device_name || 'N/A' }}</p>
        <p><strong>DevEUI:</strong> {{ device.dev_eui || 'N/A' }}</p>
        <p><strong>Tenant:</strong> {{ device.tenant_name || 'N/A' }}</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📊 Último Buffer</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Total Muestras:</strong> {{ device.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Fragmentos:</strong> {{ device.buffer_stats?.total_fragments || 0 }}</p>
        <p><strong>Promedio:</strong> {{ formatVoltage(device.buffer_stats?.avg_voltage || 0) }}V</p>
        <p><strong>Rango:</strong> {{ formatVoltage(device.buffer_stats?.min_voltage || 0) }}V - {{ formatVoltage(device.buffer_stats?.max_voltage || 0) }}V</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card voltage-card">
      <ion-card-header>
        <ion-card-title>⚡ Voltaje Actual</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <div class="voltage-display">
          <div class="voltage-value">
            {{ formatVoltage(device.buffer_stats?.current_voltage || device.buffer_stats?.avg_voltage || 0) }}V
          </div>
          <div class="voltage-status">
            <strong>Estado:</strong> {{ getVoltageStatusText() }}
          </div>
        </div>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Region:</strong> {{ device.radio_info?.rssi || 'N/A' }}dBm</p>
        <p><strong>SNR:</strong> {{ device.radio_info?.snr || 'N/A' }}dB</p>
        <p><strong>Frame:</strong> #{{ device.frame_counter || 0 }}</p>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
/**
 * VoltageDeviceInfo Component - Displays IoT device information for voltage monitoring
 * Responsibility: Present device metadata, buffer stats, and radio information
 * Specialized for voltage measurements (shows volts)
 */
defineProps({
  device: {
    type: Object,
    default: null
  }
})

// Helper function to format voltage values
const formatVoltage = (value) => {
  return (value || 0).toFixed(2)
}

const getVoltageStatusText = () => {
  const voltage = device.buffer_stats?.current_voltage || device.buffer_stats?.avg_voltage || 0
  if (voltage > 12) return 'Alto'
  if (voltage > 9) return 'Normal'
  if (voltage > 6) return 'Bajo'
  return 'Crítico'
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

.voltage-card {
  border-left: 4px solid #3b82f6;
}

.voltage-display {
  text-align: center;
  margin: 15px 0;
}

.voltage-value {
  font-size: 2rem;
  font-weight: bold;
  color: #3b82f6;
  margin-bottom: 10px;
}

.voltage-status {
  font-size: 0.9rem;
  color: #6b7280;
}

.info-card ion-card-content p {
  margin: 8px 0;
  font-size: 0.9rem;
}

.info-card ion-card-content p strong {
  color: #374151;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .device-info {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .voltage-value {
    font-size: 1.5rem;
  }
}
</style>