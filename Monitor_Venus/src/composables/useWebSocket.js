import { ref, onMounted, onUnmounted } from 'vue'

/**
 * WebSocket composable for IoT data connection
 * Handles connection, reconnection, and data processing
 */
export function useWebSocket(url = import.meta.env.VITE_WEBSOCKET_URL || 'http://localhost:8765') {
    const isConnected = ref(false)
    const websocket = ref(null)
    const reconnectAttempts = ref(0)
    const maxReconnectAttempts = 10

    // Event handlers
    const onMessage = ref(null)
    const onError = ref(null)
    const onOpen = ref(null)
    const onClose = ref(null)

    const connect = () => {
        console.log('🔄 Intentando conectar al WebSocket...')
        console.log('🌐 URL del WebSocket:', url)

        try {
            websocket.value = new WebSocket(url)

            websocket.value.onopen = (event) => {
                isConnected.value = true
                reconnectAttempts.value = 0
                console.log('🟢 Conectado al WebSocket exitosamente')
                console.log('📱 Platform: Android detection:', /android/i.test(navigator.userAgent))

                if (onOpen.value) {
                    onOpen.value(event)
                }
            }

            websocket.value.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    console.log('📥 Datos recibidos del WebSocket:', data)

                    if (onMessage.value) {
                        onMessage.value(data)
                    }
                } catch (error) {
                    console.error('❌ Error procesando mensaje del WebSocket:', error)
                    if (onError.value) {
                        onError.value(error)
                    }
                }
            }

            websocket.value.onclose = (event) => {
                isConnected.value = false
                reconnectAttempts.value++
                console.log(`🔴 WebSocket desconectado. Código: ${event.code}, Razón: ${event.reason}`)
                console.log(`🔄 Intento de reconexión #${reconnectAttempts.value}`)

                if (onClose.value) {
                    onClose.value(event)
                }

                // Auto-reconnect with exponential backoff
                if (reconnectAttempts.value <= maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
                    console.log(`⏱️ Reconectando en ${delay}ms...`)
                    setTimeout(connect, delay)
                } else {
                    console.error('🚫 Máximo de intentos de reconexión alcanzado')
                }
            }

            websocket.value.onerror = (error) => {
                console.error('❌ Error en WebSocket:', error)
                console.error('🔍 Detalles del error:', {
                    readyState: websocket.value?.readyState,
                    url: url,
                    userAgent: navigator.userAgent
                })

                if (onError.value) {
                    onError.value(error)
                }
            }

        } catch (error) {
            console.error('❌ Error creando WebSocket:', error)
            setTimeout(connect, 5000)
        }
    }

    const disconnect = () => {
        if (websocket.value) {
            websocket.value.close()
        }
    }

    const send = (data) => {
        if (websocket.value && isConnected.value) {
            websocket.value.send(JSON.stringify(data))
        } else {
            console.warn('WebSocket no está conectado')
        }
    }

    // Auto-connect on mount
    onMounted(() => {
        connect()
    })

    // Cleanup on unmount
    onUnmounted(() => {
        disconnect()
    })

    return {
        isConnected,
        reconnectAttempts,
        connect,
        disconnect,
        send,
        // Event handler setters
        setOnMessage: (handler) => { onMessage.value = handler },
        setOnError: (handler) => { onError.value = handler },
        setOnOpen: (handler) => { onOpen.value = handler },
        setOnClose: (handler) => { onClose.value = handler }
    }
}
