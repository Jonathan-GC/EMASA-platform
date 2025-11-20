<template>
    <ion-page>
        <ion-content class="ion-padding">
            <div class="notifications-view">
                <!-- Header Section -->
                <div class="header-section">
                    <h1>📨 Notificaciones</h1>
                    <div class="header-actions">
                        <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
                        <ion-button 
                            v-if="apiNotifications.length > 0" 
                            @click="fetchNotifications"
                            fill="outline"
                            size="small"
                        >
                            <ion-icon :icon="icons.refresh" slot="start" />
                            Actualizar
                        </ion-button>
                    </div>
                </div>

                <!-- Empty State -->
                <div v-if="apiNotifications.length === 0" class="empty-state">
                    <ion-card>
                        <ion-card-content>
                            <div class="empty-content">
                                <ion-icon :icon="icons.notifications" class="empty-icon" />
                                <h2>No hay notificaciones</h2>
                                <p>Cuando recibas notificaciones aparecerán aquí</p>
                            </div>
                        </ion-card-content>
                    </ion-card>
                </div>

                <!-- Notifications List -->
                <div v-else class="notifications-list">
                    <ion-card 
                        v-for="(notif, index) in apiNotifications"
                        :key="index"
                        :class="['notification-card', notif.type, { 'unread': !notif.is_read }]"
                    >
                        <ion-card-header>
                            <div class="card-header-content">
                                <div class="header-left">
                                    <ion-icon 
                                        :icon="getIcon(notif.type)" 
                                        :class="['type-icon', notif.type]"
                                    />
                                    <div class="header-text">
                                        <ion-card-title>{{ notif.title }}</ion-card-title>
                                        <ion-card-subtitle>
                                            {{ formatTime(notif.created_at || notif.timestamp) }}
                                        </ion-card-subtitle>
                                    </div>
                                </div>
                                <div class="header-right">
                                    <ion-badge 
                                        v-if="!notif.is_read" 
                                        color="primary"
                                        class="unread-badge"
                                    >
                                        Nuevo
                                    </ion-badge>
                                    <ion-button 
                                        fill="clear" 
                                        size="small"
                                        @click="removeNotification(index)"
                                    >
                                        <ion-icon :icon="icons.close" />
                                    </ion-button>
                                </div>
                            </div>
                        </ion-card-header>

                        <ion-card-content>
                            <p class="notification-message">{{ notif.message }}</p>
                        </ion-card-content>
                    </ion-card>
                </div>
            </div>
        </ion-content>
    </ion-page>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue';
import { 
    IonPage, 
    IonContent, 
    IonCard, 
    IonCardHeader, 
    IonCardTitle, 
    IonCardSubtitle,
    IonCardContent,
    IonButton,
    IonIcon,
    IonBadge
} from '@ionic/vue';
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import API from '@/utils/api/api';

// Inject icons from the global icons plugin
const icons = inject('icons', {});

// Access the global notification system from layout
const { notifications, isConnected, unreadCount, clearNotifications, removeNotification, reconnectAttempts } = inject('notifications');
const apiNotifications = ref([]);
const isLoading = ref(false);

// Fetch notifications from API
const fetchNotifications = async () => {
    isLoading.value = true;
    try {
        console.log('📡 Fetching notifications from API');
        const response = await API.get(API.MY_NOTIFICATIONS);
        
        console.log('✅ Notifications fetched:', response);
        
        // Handle array response
        if (Array.isArray(response)) {
            apiNotifications.value = response;
        } else if (response && Array.isArray(response.results)) {
            // Handle paginated response
            apiNotifications.value = response.results;
        } else {
            console.warn('⚠️ Unexpected response format:', response);
            apiNotifications.value = [];
        }
    } catch (error) {
        console.error('❌ Error fetching notifications:', error);
        apiNotifications.value = [];
    } finally {
        isLoading.value = false;
    }
};

// Get icon based on notification type
const getIcon = (type) => {
    const iconMap = {
        success: icons.success,
        warning: icons.warning,
        error: icons.error,
        info: icons.info
    };
    return iconMap[type] || icons.info;
};

const formatTime = (timestamp) => {
    if (!timestamp) return 'Fecha desconocida';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Hace un momento';
    if (diff < 3600000) return `Hace ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `Hace ${Math.floor(diff / 3600000)} h`;
    if (diff < 604800000) return `Hace ${Math.floor(diff / 86400000)} días`;
    
    return date.toLocaleDateString('es-ES', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
};

// Load notifications on mount
onMounted(() => {
    fetchNotifications();
});
</script>

<style scoped>
.notifications-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 0;
}

/* Header Section */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-section h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.connection-status {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  background: #f3f4f6;
}

.connection-status.connected {
  color: #10b981;
  background: #d1fae5;
}

.connection-status.disconnected {
  color: #ef4444;
  background: #fee2e2;
}

.connection-status ion-icon {
  font-size: 1.2rem;
  display: flex;
  align-items: center;
}

.connection-status span {
  line-height: 1;
  display: flex;
  align-items: center;
}

/* Empty State */
.empty-state {
  margin-top: 60px;
}

.empty-content {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 80px;
  color: #d1d5db;
  margin-bottom: 20px;
}

.empty-content h2 {
  font-size: 1.5rem;
  color: #6b7280;
  margin: 0 0 10px 0;
}

.empty-content p {
  font-size: 1rem;
  color: #9ca3af;
  margin: 0;
}

/* Notifications List */
.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Notification Card */
.notification-card {
  margin: 0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.notification-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.notification-card.unread {
  background: #f8fafc;
  border-left-color: #3b82f6;
}

.notification-card.success {
  border-left-color: #10b981;
}

.notification-card.warning {
  border-left-color: #f59e0b;
}

.notification-card.error {
  border-left-color: #ef4444;
}

.notification-card.info {
  border-left-color: #3b82f6;
}

/* Card Header */
.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex: 1;
}

.type-icon {
  font-size: 2rem;
  flex-shrink: 0;
  margin-top: 4px;
}

.type-icon.success {
  color: #10b981;
}

.type-icon.warning {
  color: #f59e0b;
}

.type-icon.error {
  color: #ef4444;
}

.type-icon.info {
  color: #3b82f6;
}

.header-text {
  flex: 1;
  min-width: 0;
}

ion-card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  line-height: 1.4;
}

ion-card-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.unread-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 12px;
}

/* Card Content */
ion-card-content {
  padding-top: 0;
}

.notification-message {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-section h1 {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .card-header-content {
    flex-direction: column;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .type-icon {
    font-size: 1.5rem;
  }

  ion-card-title {
    font-size: 1.1rem;
  }
}

/* Animation for new notifications */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-card {
  animation: slideIn 0.3s ease-out;
}
</style>