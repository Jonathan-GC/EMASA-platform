<template>
  <div class="device-info">
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📟 Dispositivo</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Nombre:</strong> {{ device?.device_name || 'N.A' }}</p>
        <p><strong>DevEUI:</strong> {{ device?.dev_e_ui || device?.dev_eui || 'N.A' }}</p>
        <p><strong>Tenant:</strong> {{ device?.tenant_name || 'N.A' }}</p>
      </ion-card-content>
    </ion-card>
    
    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📊 Último Buffer</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Total Muestras:</strong> {{ device?.buffer_stats?.total_samples || 0 }}</p>
        <p><strong>Fragmentos:</strong> {{ device?.buffer_stats?.total_fragments || 0 }}</p>
        <p><strong>Promedio:</strong> {{ (device?.buffer_stats?.avg_voltage || 0).toFixed(2) }}V</p>
        <p><strong>Rango:</strong> {{ (device?.buffer_stats?.min_voltage || 0).toFixed(1) }}V - {{ (device?.buffer_stats?.max_voltage || 0).toFixed(1) }}V</p>
      </ion-card-content>
    </ion-card>

    <ion-card class="info-card">
      <ion-card-header>
        <ion-card-title>📡 Radio</ion-card-title>
      </ion-card-header>
      <ion-card-content>
        <p><strong>Region:</strong> {{ device?.region || 'N.A' }}</p>
        <p><strong>Frequency:</strong> {{ device?.frequency || 'N.A' }} Hz</p>
        <p><strong>Frame:</strong> #{{ device?.f_cnt || 0 }}</p>
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

<!-- Styles moved to @/assets/css/card-styles.css -->