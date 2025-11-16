/**
 * Service Worker for Browser Notifications
 * Required for mobile browser notification support
 */

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

// Handle notification clicks - focus or open app window
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Focus existing window if available
      for (const client of clientList) {
        if ('focus' in client) return client.focus()
      }
      // Open new window if none exists
      if (self.clients.openWindow) return self.clients.openWindow('/')
    })
  )
})
