<template>
    <div class="notification-center">
        <button @click="isOpen = !isOpen" class="notification-button">
            <ion-icon :icon="icons.notifications" />
            <span v-if="unreadCount > 0" class="badge">
                {{ unreadCount > 9 ? '9+' : unreadCount }}
            </span>
            <span :class="['status-dot', isConnected ? 'connected' : 'disconnected']" />
        </button>

        <Teleport to="body">
            <div v-if="isOpen" class="notification-panel">
                <div class="panel-header">
                    <h3>Notificaciones</h3>
                    <button v-if="unreadCount > 0" @click="clearNotifications">
                        Limpiar todo
                    </button>
                </div>

                <div class="notification-list">
                    <div v-if="notifications.length === 0" class="empty-state">
                        <ion-icon :icon="icons.notifications" class="empty-icon" />
                        <p>No hay notificaciones</p>
                    </div>

                    <div
                        v-for="(notif, index) in notifications"
                        :key="index"
                        :class="['notification-item', notif.type]"
                    >
                        <ion-icon :icon="getIcon(notif.type)" class="icon" />
                        <div class="content">
                            <p class="title">{{ notif.title }}</p>
                            <p class="message">{{ notif.message }}</p>
                            <p class="time">{{ formatTime(notif.timestamp) }}</p>
                        </div>
                        <button @click="removeNotification(index)">
                            <ion-icon :icon="icons.close" />
                        </button>
                    </div>
                </div>

                <div class="panel-footer">
                    <span :class="['status', isConnected ? 'connected' : 'disconnected']">
                        {{ isConnected ? '● Conectado' : '● Desconectado' }}
                    </span>
                </div>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, inject } from 'vue';
import { useNotifications } from '@/composables/useNotifications';

// Inject icons from the global icons plugin
const icons = inject('icons', {});

const { notifications, isConnected, unreadCount, clearNotifications, removeNotification } = useNotifications();
const isOpen = ref(false);

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
    const diff = Date.now() - timestamp;
    if (diff < 60000) return 'Hace un momento';
    if (diff < 3600000) return `Hace ${Math.floor(diff / 60000)} min`;
    if (diff < 86400000) return `Hace ${Math.floor(diff / 3600000)} h`;
    return new Date(timestamp).toLocaleDateString();
};
</script>

<style scoped>
/* Estilos aquí */
</style>