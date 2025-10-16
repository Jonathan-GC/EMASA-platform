import { ref, onMounted, onUnmounted, computed } from 'vue';
import API from '@/utils/api/api';

/**
 * Notification type definition
 * @typedef {Object} Notification
 * @property {string} title
 * @property {string} message
 * @property {'info' | 'success' | 'warning' | 'error'} type
 * @property {number} timestamp
 */

export function useNotifications() {
    const notifications = ref([]);
    const connectionStatus = ref('disconnected');
    let websocket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    let reconnectTimeout = null;

    const isConnected = computed(() => connectionStatus.value === 'connected');
    const unreadCount = computed(() => notifications.value.length);

    const connect = () => {
        // Get token from API class
        const token = API.getValidToken();
        
        if (!token) {
            console.warn('⚠️ No token available for WebSocket connection');
            return;
        }

        // Clear any existing reconnect timeout
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }

        connectionStatus.value = 'connecting';

        // Build WebSocket URL with token parameter
        const wsBaseUrl = import.meta.env.VITE_WS_NOTIFY_URL || 'ws://localhost:5000/ws/notifications';
        const wsUrl = `${wsBaseUrl}?token=${token}`;

        console.log('🔔 Connecting to notification WebSocket:', wsBaseUrl);

        try {
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                console.log('✅ Notification WebSocket connected');
                connectionStatus.value = 'connected';
                reconnectAttempts = 0;
            };

            websocket.onmessage = (event) => {
                try {
                    const notification = JSON.parse(event.data);
                    console.log('📨 Notification received:', notification);

                    // Add notification to the list (keep last 50)
                    notifications.value = [notification, ...notifications.value].slice(0, 50);

                    // Browser notification
                    if ('Notification' in window && Notification.permission === 'granted') {
                        new Notification(notification.title, {
                            body: notification.message,
                            icon: '/logo.png',
                            tag: notification.timestamp?.toString() || Date.now().toString()
                        });
                    }
                } catch (error) {
                    console.error('❌ Error parsing notification message:', error);
                }
            };

            websocket.onerror = (error) => {
                console.error('❌ Notification WebSocket error:', error);
                connectionStatus.value = 'disconnected';
            };

            websocket.onclose = (event) => {
                console.log('🔴 Notification WebSocket closed:', event.code, event.reason);
                connectionStatus.value = 'disconnected';
                websocket = null;

                // Auto-reconnect if not a normal closure and under max attempts
                if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // Exponential backoff, max 30s
                    console.log(`🔄 Reconnecting notification WebSocket in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
                    
                    connectionStatus.value = 'connecting';
                    reconnectTimeout = setTimeout(() => {
                        connect();
                    }, delay);
                }
            };

        } catch (error) {
            console.error('❌ Error creating notification WebSocket:', error);
            connectionStatus.value = 'disconnected';
        }
    };

    const disconnect = () => {
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
            reconnectTimeout = null;
        }

        if (websocket) {
            console.log('🔌 Disconnecting notification WebSocket');
            websocket.close(1000, 'Client disconnect');
            websocket = null;
        }
        
        connectionStatus.value = 'disconnected';
        reconnectAttempts = 0;
    };

    const clearNotifications = () => {
        notifications.value = [];
    };

    const removeNotification = (index) => {
        notifications.value.splice(index, 1);
    };

    // Request browser notification permission
    const requestNotificationPermission = async () => {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                const permission = await Notification.requestPermission();
                console.log('🔔 Notification permission:', permission);
                return permission === 'granted';
            } catch (error) {
                console.error('❌ Error requesting notification permission:', error);
                return false;
            }
        }
        return Notification.permission === 'granted';
    };

    onMounted(() => {
        // Request notification permission if needed
        requestNotificationPermission();
        
        // Connect to WebSocket
        connect();
    });

    onUnmounted(() => {
        disconnect();
    });

    return {
        notifications,
        isConnected,
        connectionStatus,
        unreadCount,
        clearNotifications,
        removeNotification,
        requestNotificationPermission,
        connect,
        disconnect
    };
}