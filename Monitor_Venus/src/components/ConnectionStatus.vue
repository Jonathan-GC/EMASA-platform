<template>
  <div class="connection-status flex" :class="{ connected: isConnected }">
    <ion-icon :icon="isConnected ? checkmarkIcon : alertIcon" />
    {{ isConnected ? 'Conectado' : 'Desconectado' }}
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
import { inject, computed } from "vue";
import { IonIcon } from "@ionic/vue";
import { checkmarkCircle, alertCircle } from 'ionicons/icons';

const icons = inject('icons', {})

// Use fallback icons if inject fails
const checkmarkIcon = computed(() => icons.checkmarkCircle || checkmarkCircle)
const alertIcon = computed(() => icons.alertCircle || alertCircle)

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
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 0.9rem;
  background: #fee2e2;
  color: #ef4444;
  transition: all 0.3s ease;
}

.connection-status.connected {
  background: #d1fae5;
  color: #10b981;
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
