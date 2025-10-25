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
        <p><strong>Total Muestras:</strong> {{ device.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Fragmentos:</strong> {{ device.buffer_stats?.total_fragments || 0 }}</p>
        <p><strong>Promedio:</strong> {{ formatCurrent(device.buffer_stats?.avg_voltage || 0) }}A</p>
        <p><strong>Rango:</strong> {{ formatCurrent(device.buffer_stats?.min_voltage || 0) }}A - {{ formatCurrent(device.buffer_stats?.max_voltage || 0) }}A</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Region:</strong> {{ device.region || 'N/A' }}</p>
        <p><strong>Frecuencia:</strong> {{ device.frequency || 'N/A' }} dB</p>
        <p><strong>Frame:</strong> #{{ device.f_cnt || 0 }}</p>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
/**
 * CurrentDeviceInfo Component - Displays IoT device information for current monitoring
 * Responsibility: Present device metadata, buffer stats, and radio information
 * Specialized for current measurements (shows amperes instead of volts)
 */
defineProps({
  device: {
    type: Object,
    default: null
  }
})

// Helper function to format current values
const formatCurrent = (value) => {
  return (value || 0).toFixed(2)
}
</script>

<!-- Styles moved to @/assets/css/card-styles.css -->