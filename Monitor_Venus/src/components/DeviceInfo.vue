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
        <p><strong>Promedio:</strong> {{ (device.buffer_stats?.avg_voltage || 0).toFixed(2) }}V</p>
        <p><strong>Rango:</strong> {{ (device.buffer_stats?.min_voltage || 0).toFixed(1) }}V - {{ (device.buffer_stats?.max_voltage || 0).toFixed(1) }}V</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>RSSI:</strong> {{ device.radio_info?.rssi || 'N/A' }}dBm</p>
        <p><strong>SNR:</strong> {{ device.radio_info?.snr || 'N/A' }}dB</p>
        <p><strong>Frame:</strong> #{{ device.frame_counter || 0 }}</p>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
/**
 * DeviceInfo Component - Displays IoT device information
 * Responsibility: Present device metadata, buffer stats, and radio information
 */
defineProps({
  device: {
    type: Object,
    default: null
  }
})
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
}
</style>
