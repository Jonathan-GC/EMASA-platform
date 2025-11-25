import { ref, onMounted, onUnmounted, readonly } from 'vue'
import API from '@/utils/api/api'

/**
 * WebSocket composable for IoT data connection
 * Handles connection, reconnection, and data processing
 */
export function useWebSocket(deviceId = null) {
    console.log('🔧 useWebSocket composable initialized with deviceId:', deviceId)
    const isConnected = ref(false)
    const websocket = ref(null)
    const reconnectAttempts = ref(0)
    const maxReconnectAttempts = 10

    // Event handlers
    const onMessage = ref(null)
    const onError = ref(null)
    const onOpen = ref(null)
    const onClose = ref(null)

    // Get WebSocket URL from API
    const getWebSocketUrl = async () => {
        console.log('🔍 getWebSocketUrl called with deviceId:', deviceId)
        if (!deviceId) {
            console.warn('⚠️ No deviceId provided for WebSocket connection')
            return null
        }

        try {
            console.log('🔄 Fetching WebSocket URL for device:', deviceId)

            // Get access token from API
            const accessToken = API.getValidToken()
            console.log('🔑 Access token available:', !!accessToken)
            if (!accessToken) {
                console.error('❌ No valid access token available')
                return null
            }

            const endpoint = API.DEVICE_WEBSOCKET_URL(deviceId)
            console.log('📡 Making API call to:', endpoint)

            // Make request to get WebSocket URL
            console.log('📡 Making POST request to:', endpoint)
            console.log('🔑 With access token:', accessToken ? 'present' : 'missing')
            const response = await API.post(endpoint, {
                access_token: accessToken
            })

            console.log('✅ Raw API response:', response)
            console.log('✅ Response type:', typeof response)

            // Handle different response formats
            let wsUrl = null
            if (Array.isArray(response) && response.length > 0) {
                // Response is an array, get ws_url from first element
                wsUrl = response[0].ws_url || response[0].websocket_url || response[0].url
                console.log('📦 Extracted from array[0]:', wsUrl)
            } else if (typeof response === 'object' && response !== null) {
                // Response is an object
                wsUrl = response.ws_url || response.websocket_url || response.url || response
                console.log('📦 Extracted from object:', wsUrl)
            } else if (typeof response === 'string') {
                // Response is a string
                wsUrl = response
                console.log('📦 Response is string:', wsUrl)
            }

            console.log('✅ Final extracted WebSocket URL:', wsUrl)

            // Validate WebSocket URL format
            if (typeof wsUrl !== 'string' || (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://'))) {
                console.error('❌ Invalid WebSocket URL format:', wsUrl)
                return null
            }

            return wsUrl

        } catch (error) {
            console.error('❌ Error fetching WebSocket URL:', error)
            return null
        }
    }

    const connect = async () => {
        console.log('🔄 Intentando conectar al WebSocket...')

        try {
            // Get WebSocket URL from API
            const url = await getWebSocketUrl()
            if (!url) {
                console.error('❌ No WebSocket URL available')
                return
            }

            console.log('🌐 URL del WebSocket:', url)
            console.log('🔍 URL starts with ws:// or wss://:', url.startsWith('ws://') || url.startsWith('wss://'))

            websocket.value = new WebSocket(url)

            // Add connection timeout
            const connectionTimeout = setTimeout(() => {
                if (websocket.value.readyState === WebSocket.CONNECTING) {
                    console.error('⏰ WebSocket connection timeout after 10 seconds')
                    websocket.value.close()
                }
            }, 10000)

            websocket.value.onopen = (event) => {
                clearTimeout(connectionTimeout)
                isConnected.value = true
                reconnectAttempts.value = 0
                console.log('🟢 Conectado al WebSocket exitosamente')
                console.log('📱 Platform: Android detection:', /android/i.test(navigator.userAgent))
                console.log('🔗 WebSocket readyState:', websocket.value.readyState)

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
                clearTimeout(connectionTimeout)
                isConnected.value = false
                console.log('🔴 Conexión WebSocket cerrada:', event.code, event.reason)

                if (onClose.value) {
                    onClose.value(event)
                }

                // Auto-reconnect if not a normal closure and under max attempts
                if (event.code !== 1000 && reconnectAttempts.value < maxReconnectAttempts) {
                    reconnectAttempts.value++
                    console.log(`🔄 Intentando reconectar... (Intento ${reconnectAttempts.value}/${maxReconnectAttempts})`)
                    setTimeout(() => connect(), 2000 * reconnectAttempts.value) // Exponential backoff
                }
            }

            websocket.value.onerror = (error) => {
                clearTimeout(connectionTimeout)
                console.error('❌ Error en WebSocket:', error)
                console.error('🔍 WebSocket readyState:', websocket.value?.readyState)
                console.error('🔍 WebSocket URL:', url)
                isConnected.value = false  // Make sure to set disconnected on error
                if (onError.value) {
                    onError.value(error)
                }
            }

        } catch (error) {
            console.error('❌ Error al conectar WebSocket:', error)
        }
    }

    const disconnect = () => {
        if (websocket.value) {
            console.log('🔌 Desconectando WebSocket...')
            websocket.value.close(1000, 'Client disconnect')
            websocket.value = null
        }
        isConnected.value = false
        reconnectAttempts.value = 0
    }

    const send = (data) => {
        if (websocket.value && isConnected.value) {
            websocket.value.send(JSON.stringify(data))
        } else {
            console.warn('⚠️ WebSocket no conectado, no se puede enviar:', data)
        }
    }

    // Set event handlers
    const setOnMessage = (callback) => {
        onMessage.value = callback
    }

    const setOnError = (callback) => {
        onError.value = callback
    }

    const setOnOpen = (callback) => {
        onOpen.value = callback
    }

    const setOnClose = (callback) => {
        onClose.value = callback
    }

    // Cleanup on unmount
    onUnmounted(() => {
        disconnect()
    })

    // Auto-connect when component is mounted and deviceId is available
    onMounted(() => {
        if (deviceId) {
            console.log('🔌 Auto-connecting WebSocket for device:', deviceId)
            connect()
        } else {
            console.warn('⚠️ No deviceId provided, WebSocket will not auto-connect')
        }
    })

    return {
        isConnected: readonly(isConnected),
        reconnectAttempts: readonly(reconnectAttempts),
        connect,
        disconnect,
        send,
        setOnMessage,
        setOnError,
        setOnOpen,
        setOnClose
    }
}