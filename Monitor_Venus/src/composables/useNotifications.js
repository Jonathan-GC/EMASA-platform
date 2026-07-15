import { ref, onMounted, computed } from 'vue';
import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';

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
    const unreadCount = computed(() => notifications.value.length);

    // Always connected — FCM push notifications replaced the WebSocket transport.
    const isConnected = computed(() => true);
    const reconnectAttempts = computed(() => 0);

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
            await showNativeNotification(notification);
        } else {
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

            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.ready;
                await registration.showNotification(notification.title, {
                    ...options,
                    vibrate: [200, 100, 200]
                });
            } else {
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
    });

    return {
        notifications,
        isConnected,
        unreadCount,
        reconnectAttempts,
        clearNotifications,
        removeNotification,
        showNotification,
        requestNotificationPermission
    };
}
