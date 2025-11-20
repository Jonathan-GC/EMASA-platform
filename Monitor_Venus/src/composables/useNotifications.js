import { ref, onMounted, onUnmounted, computed } from 'vue';
import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';
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
    const reconnectAttempts = ref(0);
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
                reconnectAttempts.value = 0;
            };

            websocket.onmessage = async (event) => {
                try {
                    const notification = JSON.parse(event.data);
                    
                    // Add notification to the list (keep last 50)
                    notifications.value = [notification, ...notifications.value].slice(0, 50);

                    // Show notification (native or browser)
                    await showNotification(notification);
                } catch (error) {
                    console.error('Error parsing notification:', error);
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
                if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
                    reconnectAttempts.value++;
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000); // Exponential backoff, max 30s
                    console.log(`🔄 Reconnecting notification WebSocket in ${delay}ms (attempt ${reconnectAttempts.value}/${maxReconnectAttempts})`);
                    
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
        reconnectAttempts.value = 0;
    };

    const clearNotifications = () => {
        notifications.value = [];
    };

    const removeNotification = (index) => {
        notifications.value.splice(index, 1);
    };

    /**
     * Show notification (native app or browser)
     */
    const showNotification = async (notification) => {
        if (Capacitor.isNativePlatform()) {
            // Native platform - use LocalNotifications with heads-up display
            await showNativeNotification(notification);
        } else {
            // Browser - use Web Notifications API
            await showBrowserNotification(notification);
        }
    };

    /**
     * Show native notification with heads-up display
     */
    const showNativeNotification = async (notification) => {
        try {
            const permission = await LocalNotifications.checkPermissions();
            
            if (permission.display !== 'granted') {
                return;
            }

            await LocalNotifications.schedule({
                notifications: [{
                    title: notification.title,
                    body: notification.message,
                    id: Math.floor(Math.random() * 1000000),
                    schedule: { at: new Date(Date.now() + 100) },
                    channelId: 'alerts',
                    sound: 'default',
                    smallIcon: 'ic_stat_icon_config_sample',
                    largeBody: notification.message,
                    autoCancel: true,
                    ongoing: false,
                    silent: false
                }]
            });
        } catch (error) {
            console.error('Error showing native notification:', error);
        }
    };

    /**
     * Show browser notification (cross-platform compatible)
     */
    const showBrowserNotification = async (notification) => {
        if (!('Notification' in window) || Notification.permission !== 'granted') {
            return;
        }

        try {
            const options = {
                body: notification.message,
                icon: '/logo.png',
                badge: '/logo.png',
                tag: notification.timestamp?.toString() || Date.now().toString(),
                requireInteraction: false
            };

            // Use Service Worker for mobile browsers (required)
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.ready;
                await registration.showNotification(notification.title, {
                    ...options,
                    vibrate: [200, 100, 200]
                });
            } else {
                // Fallback for desktop browsers
                new Notification(notification.title, options);
            }
        } catch (error) {
            console.error('Error showing notification:', error);
        }
    };

    /**
     * Request browser notification permission
     */
    const requestNotificationPermission = async () => {
        if (!('Notification' in window)) return false;
        if (Notification.permission === 'granted') return true;
        if (Notification.permission === 'denied') return false;

        try {
            const permission = await Notification.requestPermission();
            
            // Ensure Service Worker is ready for mobile
            if (permission === 'granted' && 'serviceWorker' in navigator) {
                await navigator.serviceWorker.ready;
            }
            
            return permission === 'granted';
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    };

    onMounted(async () => {
        // Create notification channel for Android
        if (Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android') {
            try {
                await LocalNotifications.createChannel({
                    id: 'alerts',
                    name: 'Important Alerts',
                    description: 'High priority notifications that appear as heads-up',
                    importance: 4,
                    visibility: 1,
                    sound: 'default',
                    vibration: true,
                    lights: true,
                    lightColor: '#FF0000'
                });
            } catch (error) {
                console.error('Error creating notification channel:', error);
            }
        }

        await requestNotificationPermission();
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
        reconnectAttempts,
        clearNotifications,
        removeNotification,
        requestNotificationPermission,
        connect,
        disconnect
    };
}