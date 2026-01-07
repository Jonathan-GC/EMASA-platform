<template>
  <div class="device-info">
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📟 Dispositivo</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Nombre:</strong> {{ device?.device_name || 'N.A' }}</p>
        <p><strong>DevEUI:</strong> {{ device?.dev_eui || 'N.A' }}</p>
        <p><strong>Tenant:</strong> {{ device?.tenant_id || 'N.A' }}</p>
      </ion-card-content>
    </ion-card>
    
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📊 Último Buffer</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Muestras:</strong> {{ device?.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Promedio:</strong> {{ formatVoltage(device?.buffer_stats?.avg_value || 0) }}V</p>
        <p><strong>Valor:</strong> {{ formatVoltage(device?.buffer_stats?.max_voltage || 0) }}V</p>
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
        <p><strong>Region:</strong> {{ device?.region || 'N.A' }}</p>
        <p><strong>Frecuencia:</strong> {{ device?.radio_info?.snr || 'N.A' }} Hz</p>
        <p><strong>Frame:</strong> #{{ device?.f_cnt || 0 }}</p>
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

<!-- Styles moved to @/assets/css/card-styles.css -->