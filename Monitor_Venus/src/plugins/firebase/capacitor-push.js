import { PushNotifications } from '@capacitor/push-notifications'
import { Capacitor } from '@capacitor/core'
import API from '@/utils/api/api'

/**
 * Initialize Capacitor native push notifications (Android/iOS).
 * Requests permission, registers with APNs/FCM, and sends the token to the backend.
 * Returns the FCM token on success, null on failure.
 */
export async function initCapacitorPush() {
  if (!Capacitor.isNativePlatform()) return null

  let permission = await PushNotifications.checkPermissions()

  if (permission.receive === 'prompt') {
    permission = await PushNotifications.requestPermissions()
  }

  if (permission.receive !== 'granted') {
    console.warn('Push notification permission not granted on native')
    return null
  }

  await PushNotifications.register()

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Push registration timeout — no native event received'))
    }, 10000)

    PushNotifications.addListener('registration', (token) => {
      clearTimeout(timeout)
      console.log('Capacitor push registration token:', token.value)
      resolve(token.value)
    })

    PushNotifications.addListener('registrationError', (err) => {
      clearTimeout(timeout)
      console.error('Capacitor push registration error:', err.error)
      reject(err.error)
    })
  })
}

/**
 * Listen for push notifications received while the app is in the foreground (native).
 * The callback receives the Capacitor PushNotification object.
 * Returns a remove function to clean up the listener.
 */
export async function listenForegroundNotifications(callback) {
  const handle = await PushNotifications.addListener('pushNotificationReceived', callback)
  return () => handle.remove()
}

/**
 * Listen for notification action taps (user tapped the notification).
 * The callback receives the PushNotificationActionPerformed object.
 * Returns a remove function.
 */
export async function handleNotificationActions(callback) {
  const handle = await PushNotifications.addListener('pushNotificationActionPerformed', callback)
  return () => handle.remove()
}

/**
 * Register the native FCM token with the Django backend.
 * Returns the device object from the API.
 */
export async function registerDeviceOnBackend(fcmToken) {
  const platform = Capacitor.getPlatform() // 'android' or 'ios'
  const response = await API.post(API.REGISTER_DEVICE, {
    fcm_token: fcmToken,
    platform
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
