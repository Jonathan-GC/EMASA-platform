<template>
    <ion-page>
        <ion-content class="ion-padding">
            <div class="notifications-view">
                <!-- Header with connection status -->
                <div class="header">
                    <div class="header-title">
                        <ion-back-button default-href="/home"></ion-back-button>
                        <h1>
                            <ion-icon :icon="icons.notifications"></ion-icon>
                            Notificaciones
                        </h1>
                    </div>
                    <div class="header-actions">
                        <ConnectionStatus :is-connected="isConnected" :reconnect-attempts="reconnectAttempts" />
                        <ion-button 
                            v-if="apiNotifications.length > 0" 
                            @click="() => fetchNotifications(1)"
                            fill="outline"
                            size="small"
                            :disabled="isLoading"
                        >
                            <ion-spinner v-if="isLoading" name="crescent" />
                            <ion-icon v-else :icon="icons.refresh" slot="start" />
                            {{ isLoading ? 'Cargando...' : 'Actualizar' }}
                        </ion-button>
                    </div>
                </div>

                <!-- Loading State -->
                <div v-if="isLoading" class="loading-state">
                    <ion-card>
                        <ion-card-content>
                            <div class="loading-content">
                                <ion-spinner name="crescent" color="primary" />
                                <p>Cargando notificaciones...</p>
                            </div>
                        </ion-card-content>
                    </ion-card>
                </div>

                <!-- Empty State -->
                <div v-else-if="apiNotifications.length === 0 && !isLoading" class="empty-state">
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
                <div v-else-if="!isLoading" class="notifications-list">
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

                <!-- Pagination Controls -->
                <div v-if="totalPages > 1" class="pagination-controls">
                    <ion-button
                        fill="outline"
                        :disabled="currentPage === 1 || isLoading"
                        @click="goToPage(currentPage - 1)"
                    >
                        <ion-icon :icon="icons.chevronBack" slot="start" />
                        Anterior
                    </ion-button>
                    
                    <div class="pagination-info">
                        <span class="page-indicator">Página {{ currentPage }} de {{ totalPages }}</span>
                        <span class="items-info">{{ apiNotifications.length }} de {{ totalCount }} notificaciones</span>
                    </div>
                    
                    <ion-button
                        fill="outline"
                        :disabled="currentPage === totalPages || isLoading"
                        @click="goToPage(currentPage + 1)"
                    >
                        Siguiente
                        <ion-icon :icon="icons.chevronForward" slot="end" />
                    </ion-button>
                </div>
            </div>
        </ion-content>
    </ion-page>
</template>

<script setup>
import { ref, inject, onMounted, computed } from 'vue';
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
    IonBadge,
    IonSpinner,
    IonBackButton
} from '@ionic/vue';
import ConnectionStatus from '@/components/ConnectionStatus.vue'
import API from '@/utils/api/api';

// Inject icons from the global icons plugin
const icons = inject('icons', {});

// Access the global notification system from layout
const { notifications, isConnected, unreadCount, clearNotifications, removeNotification, reconnectAttempts } = inject('notifications');
const allNotifications = ref([]);
const isLoading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);

// Computed property to get paginated notifications
const apiNotifications = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    const end = start + pageSize.value;
    return allNotifications.value.slice(start, end);
});

const totalCount = computed(() => allNotifications.value.length);
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value));

// Fetch notifications from API
const fetchNotifications = async (page = 1) => {
    isLoading.value = true;
    try {
        console.log(`📡 Fetching notifications from API - Page ${page}`);
        
        // Build URL with query parameters
        const url = `${API.MY_NOTIFICATIONS}?page=${page}&page_size=${pageSize.value}`;
        const response = await API.get(url);
        
        console.log('✅ Notifications fetched:', response);
        
        // Handle paginated response with count
        if (response && typeof response === 'object' && 'count' in response && Array.isArray(response.results)) {
            allNotifications.value = response.results;
        } 
        // Handle simple array response
        else if (Array.isArray(response)) {
            allNotifications.value = response;
        } 
        // Handle unexpected format
        else {
            console.warn('⚠️ Unexpected response format:', response);
            allNotifications.value = [];
        }
        
        // Reset to page 1 after fetching
        currentPage.value = 1;
        
        console.log(`📊 Pagination: Page ${currentPage.value}/${totalPages.value}, Total: ${totalCount.value}, Showing: ${apiNotifications.value.length}`);
    } catch (error) {
        console.error('❌ Error fetching notifications:', error);
        allNotifications.value = [];
        currentPage.value = 1;
    } finally {
        isLoading.value = false;
    }
};

// Navigate to specific page
const goToPage = (page) => {
    if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page;
        // Scroll to top when changing pages
        window.scrollTo({ top: 0, behavior: 'smooth' });
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
@import '@assets/css/dashboard.css';

.notifications-view {
  width: 100%;
  padding: 20px;
}

/* Header Section */
.header {
  margin-bottom: 30px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
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

/* Loading State */
.loading-state {
  margin-top: 20px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
}

.loading-content ion-spinner {
  width: 48px;
  height: 48px;
}

.loading-content p {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* Notifications List */
.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Notification Card */
.notification-card {
  margin: 0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.notification-card:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
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
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.type-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  margin-top: 2px;
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
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
  line-height: 1.3;
}

ion-card-subtitle {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.unread-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 3px 10px;
}

/* Card Content */
ion-card-content {
  padding-top: 0;
  padding: 12px 16px;
}

.notification-message {
  font-size: 0.9rem;
  color: #4b5563;
  line-height: 1.5;
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

/* Pagination Controls */
.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  gap: 16px;
}

.pagination-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.page-indicator {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.items-info {
  font-size: 0.875rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .pagination-controls {
    flex-direction: column;
    gap: 12px;
  }

  .pagination-info {
    order: -1;
    width: 100%;
  }

  .pagination-controls ion-button {
    flex: 1;
    min-width: 120px;
  }
}
</style>