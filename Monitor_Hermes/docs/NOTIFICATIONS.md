# Notifications WebSocket

## Description

The `/ws/notifications` endpoint is a WebSocket channel dedicated **exclusively** to receive personal user notifications.

## Connection

### URL
```
ws://host:port/ws/notifications?token=JWT_TOKEN
```

### Authentication
A valid JWT is required in the `token` query parameter. The token must contain:
- `user_id`: User ID
- `username`: Username

## Message Format

### Received notifications (from server)
```json
{
    "channel": "notifications",
    "title": "Notification title",
    "message": "Message content",
    "type": "info|warning|error|success"
}
```

#### Notification types
- `info`: General information
- `warning`: Warning
- `error`: Error or issue
- `success`: Successful action

### Client messages (to server)

#### Heartbeat (keep connection alive)
```json
{
    "action": "ping"
}
```

Server response:
```json
{
    "action": "pong"
}
```

#### Acknowledge notification receipt
```json
{
    "action": "ack",
    "notification_id": "optional_notification_id"
}
```

## Sending Notifications from Another API

### Endpoint to send notification
```
POST http://{HERMES_API_URL}/notify
```

### Payload
```json
{
    "user_id": "123",
    "title": "New alert",
    "message": "An anomaly was detected in sensor X",
    "type": "warning"
}
```

## WebSocket Connections Architecture

```
Frontend Client can have multiple simultaneous connections:

┌─────────────────────────────────────────────────────────────┐
│  Client (Browser/App)                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [WS1] ws://host/ws/notifications                           │
│         └─> ✉️  Personal user notifications                 │
│                                                             │
│  [WS2] ws://host/ws/tenant/{tenant_id}                      │
│         └─> 📊 MQTT data from all tenant devices            │
│                                                             │
│  [WS3] ws://host/ws/device/{device_id}                      │
│         └─> 📡 Specific device data                         │
│                                                             │
│  [WS4] ws://host/ws (optional, legacy)                      │
│         └─> 🔀 Multipurpose connection                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

### 1. Automatic reconnection
Implement reconnection logic in case of disconnection:
```javascript
let reconnectInterval = 1000; // Start with 1 second
const maxReconnectInterval = 30000; // Maximum 30 seconds

function reconnectNotifications() {
    setTimeout(() => {
        console.log('🔄 Attempting to reconnect...');
        connectNotifications();
        reconnectInterval = Math.min(reconnectInterval * 2, maxReconnectInterval);
    }, reconnectInterval);
}
```

### 2. Periodic heartbeat
Send ping every 30 seconds to keep connection alive:
```javascript
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }));
    }
}, 30000);
```

### 3. Error handling
```javascript
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Don't close immediately, wait for onclose
};

ws.onclose = (event) => {
    if (event.code === 1008) {
        console.error('❌ Authentication failed, get new token');
        // Refresh token and reconnect
    } else {
        console.log('🔌 Connection closed, reconnecting...');
        reconnectNotifications();
    }
};
```

### 4. Notification management in UI
```javascript
function showNotification(title, message, type) {
    // Use browser notification API
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: getIconForType(type),
            tag: 'hermes-notification'
        });
    }
    
    // Display in UI (toast, banner, etc.)
    displayInAppNotification({ title, message, type });
    
    // Save to local history
    saveNotificationToHistory({ title, message, type, timestamp: Date.now() });
}
```

## WebSocket Close Codes

- `1008`: Policy violation (invalid or expired token)
- `500`: Internal server error
- `1000`: Normal closure
- `1006`: Connection lost (no close handshake)

## Testing

See example file: `tests/test_notifications_ws.py`

## Differences with Other Endpoints

| Endpoint            | Purpose                | Receives                    |
| ------------------- | ---------------------- | --------------------------- |
| `/ws/notifications` | Personal notifications | Only user notifications     |
| `/ws`               | General tenant data    | MQTT data, tenant broadcast |
| `/ws/tenant/{id}`   | Tenant dashboard       | All tenant devices          |
| `/ws/device/{id}`   | Device monitoring      | Only that device's data     |

## FAQ

### Can I connect to multiple endpoints simultaneously?
Yes, it's the recommended practice. Each connection has a specific purpose.

### Are notifications persisted if the user is not connected?
No, currently notifications are only sent to active connections. For persistence, you must implement a queue system in the API that sends the notifications.

### Can I receive notifications on the general `/ws` endpoint?
Yes, if the user has `user_id` in their token, they can also receive notifications there, but mixing purposes is not recommended.

### How do I know if my notification was delivered?
The `/notify` endpoint responds with:
```json
{
    "status": "success|error",
    "sent": true|false
}
```
`sent: true` means there was at least one active user connection.
