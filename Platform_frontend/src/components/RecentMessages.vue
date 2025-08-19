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
          <span class="samples">{{ getSampleCount(message) }} muestras</span>
          <span class="fragment">
            Frag: {{ message.object?.fragment_number || 'N/A' }}/{{ message.object?.total_fragments || 'N/A' }}
          </span>
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
    return format(new Date(timestamp), 'HH:mm:ss')
  } catch {
    return 'N/A'
  }
}

const getSampleCount = (message) => {
  return message.object?.values?.length || message.measurement_values?.length || 0
}
</script>

<style scoped>
.recent-messages {
  margin-top: 30px;
  font-family: monospace;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.9rem;
}

.timestamp {
  font-weight: 100;
  color: #95a1adff;
  min-width: 70px;
}

.device {
  
  font-weight: 500;
  color: #495057;
  flex: 1;
}

.samples {
  background: #e7ffedff;
  color: #28a745;
  font-weight: 500;
  min-width: 80px;
  padding: 2px 6px;
  order-radius: 4px;
  font-size: 0.8em;
}

.fragment {
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.8em;
  min-width: 80px;
  text-align: center;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .message-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .timestamp,
  .samples,
  .fragment {
    min-width: unset;
  }
}
</style>
