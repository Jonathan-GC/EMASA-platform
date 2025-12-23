<template>
  <div class="device-info" v-if="device">
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📟 Dispositivo</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Nombre:</strong> {{ device.device_name || 'N.A' }}</p>
        <p><strong>DevEUI:</strong> {{ device.dev_eui || 'N.A' }}</p>
        <p><strong>Tenant:</strong> {{ device.tenant_name || 'N.A' }}</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📊 Último Buffer - {{ capitalizeFirst(measurement.unit) }}</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Total Muestras:</strong> {{ device.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Fragmentos:</strong> {{ device.buffer_stats?.total_fragments || 0 }}</p>
        <p><strong>Promedio:</strong> {{ formatValue(device.buffer_stats?.[`avg_${measurement.unit.toLowerCase()}`] || 0) }} {{ measurement.ref }}</p>
        <p><strong>Rango:</strong> {{ formatValue(device.buffer_stats?.[`min_${measurement.unit.toLowerCase()}`] || 0) }} {{ measurement.ref }} - {{ formatValue(device.buffer_stats?.[`max_${measurement.unit.toLowerCase()}`] || 0) }} {{ measurement.ref }}</p>
      </ion-card-content>
    </ion-card>


    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Región:</strong> {{ device.payload?.radio_info?.rssi || device.region || 'N.A' }}</p>
        <p><strong>Frecuencia:</strong> {{ device.payload?.radio_info?.snr || device.frequency || 'N.A' }} Hz</p>
        <p><strong>Frame:</strong> #{{ device.payload?.frame_counter || device.f_cnt || 0 }}</p>
      </ion-card-content>
    </ion-card>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { capitalizeFirst } from '@utils/formatters/formatters.js'

/**
 * MeasurementDeviceInfo Component - Displays IoT device information for any measurement type
 * Responsibility: Present device metadata, buffer stats, and radio information
 * Dynamic component that adapts to the measurement type
 */
const props = defineProps({
  device: {
    type: Object,
    default: null
  },
  measurement: {
    type: Object,
    required: true
  }
})

const icons = inject('icons', {})

// Helper function to format measurement values
const formatValue = (value) => {
    console.log('device: ', props.device)
  return (value || 0).toFixed(2)
  
  
}

const getMeasurementStatusText = () => {
  if (!props.device?.buffer_stats || !props.measurement) return 'N.A'
  
  const measurementKey = props.measurement.unit.toLowerCase()
  const currentValue = props.device.buffer_stats[`current_${measurementKey}`] || 
                       props.device.buffer_stats[`avg_${measurementKey}`] || 0
  
  const min = props.measurement.min
  const max = props.measurement.max
  const threshold = props.measurement.threshold
  
  if (currentValue < min + threshold) return 'Bajo'
  if (currentValue > max - threshold) return 'Alto'
  if (currentValue > max - (threshold * 2)) return 'Advertencia'
  return 'Normal'
}
</script>

<!-- Styles moved to @/assets/css/card-styles.css -->
