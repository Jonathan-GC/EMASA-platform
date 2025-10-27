<template>
  <ion-card class="recent-messages" v-if="messages.length > 0">
    <ion-card-header>
      <ion-card-title>📨 Mensajes Recientes</ion-card-title>
    </ion-card-header>
    <ion-card-content>
      <div class="message-list">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          class="message-item"
        >
          <span class="timestamp">{{ formatTime(message.reception_timestamp) }}</span>
          <span class="device">{{ message.device_name }}</span>
          <span class="samples">{{ message.buffer_stats?.total_samples  }} muestras</span>
          <!--<span class="fragment">
            Frag: {{ message.object?.fragment_number || 'N.A' }}/{{ message.object?.total_fragments || 'N.A' }}
          </span>-->
        </div>
      </div>
    </ion-card-content>
  </ion-card>
</template>

<script setup>
import { format } from 'date-fns'

/**
 * RecentMessages Component - Displays recent WebSocket messages
 * Responsibility: Show recent message history with timestamps and metadata
 */
defineProps({
  messages: {
    type: Array,
    default: () => []
  }
})

// Helper functions
const formatTime = (timestamp) => {
  try {
    // Convertir timestamp a zona horaria local explícitamente
    const date = new Date(timestamp)
    // Usar toLocaleTimeString para forzar zona horaria local
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false 
    })
  } catch {
    return 'N.A'
  }
}

const getSampleCount = (message) => {
  // Handle WebSocket data structure: count samples across all channels
  if (message.object?.measurements) {
    let totalSamples = 0
    Object.values(message.object.measurements).forEach(sensorData => {
      if (typeof sensorData === 'object') {
        Object.values(sensorData).forEach(channelData => {
          if (Array.isArray(channelData)) {
            totalSamples += channelData.length
          }
        })
      }
    })
    return totalSamples
  }
  
  // Fallback to old structure
  return message.object?.values?.length || message.measurement_values?.length || 0
}
</script>

<!-- Styles moved to @/assets/css/card-styles.css -->