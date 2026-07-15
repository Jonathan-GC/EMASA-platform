import { getMessaging, getToken, onMessage } from 'firebase/messaging'
import { firebaseApp } from '@/plugins/firebase/index'
import API from '@/utils/api/api'

let messagingInstance = null

function getMessagingInstance() {
  if (!messagingInstance) {
    messagingInstance = getMessaging(firebaseApp)
  }
  return messagingInstance
}

/**
 * Request browser notification permission and obtain FCM token.
 * Returns the FCM token string or null if permission was denied.
 */
export async function requestWebPushPermission() {
  console.log('🔔 requestWebPushPermission called, current permission:', Notification.permission)

  const permission = await Notification.requestPermission()
  console.log('🔔 Notification permission after request:', permission)

  if (permission !== 'granted') {
    console.warn('Push notification permission denied')
    return null
  }

  const messaging = getMessagingInstance()
  const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY
  console.log('🔔 VAPID key present:', !!vapidKey, 'starts with:', vapidKey ? vapidKey.substring(0, 10) + '...' : 'N/A')

  if (!vapidKey || vapidKey === 'REPLACE_WITH_YOUR_VAPID_KEY') {
    console.error('VITE_FIREBASE_VAPID_KEY is not configured in .env')
    return null
  }

  try {
    const token = await getToken(messaging, { vapidKey })
    console.log('FCM web token obtained:', token)
    return token
  } catch (error) {
    console.error('🔔 Error getting FCM token:', error)
    return null
  }
}

/**
 * Listen for foreground push messages.
 * The callback receives the Firebase message payload.
 * Returns an unsubscribe function.
 */
export function onForegroundMessage(callback) {
  const messaging = getMessagingInstance()
  return onMessage(messaging, callback)
}

/**
 * Register the FCM token with the Django backend.
 * Returns the device object from the API (includes `id` for later unregistration).
 */
export async function registerDeviceOnBackend(fcmToken) {
  const response = await API.post(API.REGISTER_DEVICE, {
    fcm_token: fcmToken,
    platform: 'web'
  })
  return response
}

/**
 * Unregister a device from the Django backend by device ID.
 */
export async function unregisterDeviceFromBackend(deviceId) {
  const response = await API.post(API.UNREGISTER_DEVICE(deviceId), {
    is_active: false
  })
  return response
}
