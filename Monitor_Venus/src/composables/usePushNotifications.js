import { ref } from 'vue'
import { Capacitor } from '@capacitor/core'
import * as webPush from '@/plugins/firebase/messaging'
import * as nativePush from '@/plugins/firebase/capacitor-push'

const isPushSupported = !!(('Notification' in window) || Capacitor.isNativePlatform())
const isNative = Capacitor.isNativePlatform()

const fcmToken = ref(null)
const deviceId = ref(localStorage.getItem('push_device_id') || null)
const isRegistered = ref(!!localStorage.getItem('push_device_id'))

function persistDeviceId(id) {
  deviceId.value = id
  localStorage.setItem('push_device_id', id)
}

function clearDeviceId() {
  deviceId.value = null
  localStorage.removeItem('push_device_id')
}

function persistFcmToken(token) {
  fcmToken.value = token
  localStorage.setItem('push_fcm_token', token)
}

function clearFcmToken() {
  fcmToken.value = null
  localStorage.removeItem('push_fcm_token')
}

/**
 * Request permission and register the device for push notifications.
 * Web: gets FCM token via Firebase SDK, sends to backend.
 * Native: uses Capacitor PushNotifications, sends token to backend.
 */
export async function registerPush() {
  console.log('🔔 registerPush called, isPushSupported:', isPushSupported, 'isNative:', isNative)

  if (!isPushSupported) {
    console.warn('Push notifications not supported on this platform')
    return false
  }

  if (isRegistered.value && deviceId.value) {
    console.log('Push already registered, device:', deviceId.value)
    return true
  }

  try {
    let token
    let deviceResponse

    if (isNative) {
      console.log('🔔 Native path: calling initCapacitorPush')
      token = await nativePush.initCapacitorPush()
      if (!token) {
        console.warn('🔔 Native push token is null/undefined')
        return false
      }
      console.log('🔔 Native token obtained, registering on backend...')
      deviceResponse = await nativePush.registerDeviceOnBackend(token)
    } else {
      console.log('🔔 Web path: calling requestWebPushPermission')
      token = await webPush.requestWebPushPermission()
      if (!token) {
        console.warn('🔔 Web push token is null/undefined')
        return false
      }
      console.log('🔔 Web token obtained, registering on backend...')
      deviceResponse = await webPush.registerDeviceOnBackend(token)
    }

    console.log('🔔 Backend response:', deviceResponse)
    persistFcmToken(token)

    if (deviceResponse && deviceResponse.id) {
      persistDeviceId(deviceResponse.id)
    }

    isRegistered.value = true
    console.log('Push notifications registered successfully')
    return true
  } catch (error) {
    console.error('Error registering push notifications:', error)
    return false
  }
}

/**
 * Unregister the device from push notifications.
 * Calls the backend to deactivate the device record.
 */
export async function unregisterPush() {
  if (!deviceId.value) {
    console.log('No device ID to unregister')
    return
  }

  try {
    if (isNative) {
      await nativePush.unregisterDeviceFromBackend(deviceId.value)
    } else {
      await webPush.unregisterDeviceFromBackend(deviceId.value)
    }
    console.log('Push device unregistered successfully')
  } catch (error) {
    console.error('Error unregistering push device:', error)
  } finally {
    clearDeviceId()
    clearFcmToken()
    isRegistered.value = false
  }
}

/**
 * Listen for push notifications received while the app is in the foreground.
 * The callback receives a notification-like object with `title` and `body`.
 * Returns a cleanup function to remove the listener.
 */
export async function listenForeground(callback) {
  if (isNative) {
    return nativePush.listenForegroundNotifications((notification) => {
      callback({
        title: notification.title || '',
        body: notification.body || '',
        data: notification.data || {}
      })
    })
  }

  const unsubscribe = webPush.onForegroundMessage((payload) => {
    const notification = payload.notification || {}
    callback({
      title: notification.title || '',
      body: notification.body || '',
      data: payload.data || {}
    })
  })

  return () => unsubscribe()
}

export function usePushNotifications() {
  return {
    isPushSupported,
    isNative,
    fcmToken,
    deviceId,
    isRegistered,
    registerPush,
    unregisterPush,
    listenForeground
  }
}
