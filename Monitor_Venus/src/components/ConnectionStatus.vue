<template>
  <div class="connection-status" :class="{ connected: isConnected }">
  <ion-icon :icon="isConnected ? icons.checkmarkCircle : icons.alertCircle" />
  {{ isConnected ? 'Conectado' : 'Desconectado' }}
    <!--<ion-icon :icon="info" v-if="isConnected" />
    <ion-icon :icon="warning" v-else />

    {{ isConnected ? 'Conectado' : ' Desconectado' }}-->
    <span v-if="!isConnected && reconnectAttempts > 0" class="reconnect-info">
      (Intento {{ reconnectAttempts }}/10)
    </span>
  </div>
</template>

<script setup>
/**
 * ConnectionStatus Component - Shows WebSocket connection status
 * Responsibility: Display connection state and reconnection attempts
 */
import {inject} from "vue";
import { IonIcon } from "@ionic/vue";
const icons = inject('icons', {})
defineProps({
  isConnected: {
    type: Boolean,
    default: false
  },
  reconnectAttempts: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.connection-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 0.9rem;
  background: #fee;
  color: #dc3545;
  border: 1px solid #f5c6cb;
  transition: all 0.3s ease;
}

.connection-status.connected {
  background: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

.reconnect-info {
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Animation for disconnected state */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.connection-status:not(.connected) {
  animation: pulse 2s infinite;
}
</style>
