/**
 * Firebase Cloud Messaging Service Worker
 *
 * This file is a template. %%VITE_*%% placeholders are replaced at dev/build
 * time by the Vite SW plugin so that Firebase credentials are never committed
 * to the repository.
 */

importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js')
importScripts('https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js')

firebase.initializeApp({
  apiKey: '%%VITE_FIREBASE_API_KEY%%',
  authDomain: '%%VITE_FIREBASE_AUTH_DOMAIN%%',
  projectId: '%%VITE_FIREBASE_PROJECT_ID%%',
  messagingSenderId: '%%VITE_FIREBASE_MESSAGING_SENDER_ID%%',
  appId: '%%VITE_FIREBASE_APP_ID%%'
})

const messaging = firebase.messaging()

messaging.onBackgroundMessage((payload) => {
  console.log('[SW] Background notification received:', payload)

  const notificationTitle = (payload.notification && payload.notification.title) || 'Notification'
  const notificationOptions = {
    body: (payload.notification && payload.notification.body) || '',
    icon: '/logo.png',
    badge: '/logo.png',
    data: payload.data || {}
  }

  self.registration.showNotification(notificationTitle, notificationOptions)
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if ('focus' in client) return client.focus()
        }
        if (self.clients.openWindow) return self.clients.openWindow('/')
      })
  )
})
