// Helper to get API base URL from env or fallback
function getApiBaseUrl() {
    const base = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL)
        ? import.meta.env.VITE_API_URL
        : 'http://localhost:8000/api/';
    return String(base);
}

class API {
    static instance = null;

    API_VERSION = 'v1/';
    API_BASE_URL = getApiBaseUrl() + 'v1/';

    _accessToken = null;
    _refreshToken = null;
    _tokenExpiry = null;

    // Configuración de almacenamiento
    USE_PERSISTENT_STORAGE = true; // Cambiar a false para solo memoria

    // Queue for failed requests during token refresh
    isRefreshing = false;
    failedQueue = [];

    //====[ENDPOINTS]====
    //----[USERS]----
    USER = 'users/user/'
    ME = 'users/user/me/'
    ACTIVATE_USER(userId) {
        return `users/user/${userId}/enable_user/`
    }
    DEACTIVATE_USER(userId) {
        return `users/user/${userId}/disable_user/`
    }

    //----[AUTH]----
    TOKEN = 'token/'
    REFRESH_TOKEN = 'token/refresh/'
    CSRF_TOKEN = 'csrf/'
    LOGOUT = 'logout/';
    REGISTER = 'users/auth/register/';
    VERIFY_ACCOUNT = 'users/auth/verify-account/'
    RESEND_VERIFICATION = 'users/auth/re-send-verification/'
    RESET_PASSWRORD_REQUEST = 'users/auth/request-password-reset/';
    RESET_PASSWORD_CONFIRM = 'users/auth/reset-password-confirm/';

    //----[ORGANIZATIONS]----
    TENANT = 'organizations/tenant/'
    WORKSPACE = 'organizations/workspace/'
    SUBSCRIPTION = 'organizations/subscription/'

    //----[ROLES]----
    ROLE = 'roles/role/'
    ROLE_PERMISSION = 'roles/role-permission/'
    ROLE_MEMBERSHIP(roleId) {
        return `roles/role/${roleId}/get_all_role_users/`
    }
    PERMISSION_KEY = 'roles/permission-key/'
    WORKSPACE_MEMBERSHIP = 'roles/workspace-membership/'
    ASSIGNABLE_PERMISSIONS(roleId) {
        return `roles/role/${roleId}/get_assignable_permissions/`
    }
    BULK_ASSIGN_PERMISSIONS(roleId) {
        return `roles/role/${roleId}/bulk_assign_permissions/`
    } 

    //----[INFRACSTRUCTURE]----
    DEVICE = 'infrastructure/device/'
    GATEWAY = 'infrastructure/gateway/'
    DEVICE_TYPE = 'infrastructure/type/'
    MACHINE = 'infrastructure/machine/'
    APPLICATION = 'infrastructure/application/'
    LOCATION = 'infrastructure/location/'
    DEVICE_PROFILE_TEMPLATE = '/device-profile-template/'
    DEVICE_TYPES = 'infrastructure/type/'
    DEVICE_SET_ACTIVATION_KEYS(deviceId) {
        return `infrastructure/device/${deviceId}/set_activation/`
    }

    DEVICE_ACTIVATION_DETAILS(deviceId) {
        return `infrastructure/device/${deviceId}/activation_details/`
    }

    DEVICE_ACTIVATION(deviceId) {
        return `infrastructure/device/${deviceId}/activate/`
    }

    DEVICE_DEACTIVATION(deviceId) {
        return `infrastructure/device/${deviceId}/deactivate/`
    }

//----[MEASUREMENTS]----
    DEVICE_GET_MEASUREMENTS(deviceId) {
        return `infrastructure/device/${deviceId}/measurements/`
    }

    DEVICE_CREATE_MEASUREMENTS(deviceId) {
        return `infrastructure/device/${deviceId}/create_measurement/`
    }
    DEVICE_LAST_MEASUREMENT(deviceId) {
        return `infrastructure/device/${deviceId}/last_metrics/`
    }
    DEVICE_HISTORICAL_MEASUREMENTS(deviceId) {
        return `infrastructure/device/${deviceId}/historical_aggregated_metrics/`
    }
    DETAILED_POINTS(deviceId) {
        return `infrastructure/device/${deviceId}/historic_metrics/`
    }
    DEVICE_UPDATE_MEASUREMENTS='infrastructure/device/update_measurement/'


    //----[WEBSOCKET]----
    

    // ===== MÉTODOS PARA ENDPOINTS DINÁMICOS =====
    // Usar estos en lugar de constantes para rutas con IDs

    /**
     * Endpoint para dispositivos de una aplicación
     * @param {string|number} applicationId - ID de la aplicación
     * @returns {string} - Endpoint completo
     */
    APPLICATION_DEVICES(applicationId) {
        return `infrastructure/application/${applicationId}/devices/`
    }

    /**
     * Endpoint para un dispositivo específico de una aplicación
     * @param {string|number} applicationId - ID de la aplicación
     * @param {string|number} deviceId - ID del dispositivo
     * @returns {string} - Endpoint completo
     */
    APPLICATION_DEVICE_DETAIL(applicationId, deviceId) {
        return `infrastructure/application/${applicationId}/devices/${deviceId}/`
    }

    /**
     * Endpoint para dispositivos de un gateway
     * @param {string|number} gatewayId - ID del gateway
     * @returns {string} - Endpoint completo
     */
    GATEWAY_DEVICES(gatewayId) {
        return `infrastructure/gateway/${gatewayId}/devices/`
    }

    DEVICE_WEBSOCKET_URL(deviceId) {
        return `infrastructure/device/${deviceId}/get_ws_link/`
    }
    //----[CHIRPSTACK]----
    DEVICE_PROFILE = 'chirpstack/device-profile/'
    TENANT_USER = 'chirpstack/tenant-user/'
    API_USER = 'chirpstack/api-user/'

    //----[SPECIAL]----
    GEN_OBJECT_PERMISSION_KEY = 'regenerate_permission_keys/'

    //----[NOTIFICATION]----
    MY_NOTIFICATIONS = 'support/notification/my_notifications/'
    

    //----[SUPPORT]----
    SUPPORT_TICKET = 'support/ticket/'
    ATTACMEENT_CREATE = 'support/attachment/'
    GET_TYPES = 'support/ticket/get_all_types/'


    //----[INBOX]----
    SUPPORT_MEMBERS = 'support/ticket/get_support_members/'

    INBOX_READ(ticketId) {
        return `support/ticket/${ticketId}/mark_as_read/`
    }
    
    DELEGATE(ticketId){
        return `support/ticket/${ticketId}/delegate/`
    }

    //----[CONVERSATION]----

    TICKET_CONVERSATION(ticketId) {
        return `support/ticket/${ticketId}/conversation/`
    }

    COMMENT = 'support/comment/'
    COMMENT_ATTACHMENT = 'support/comment-attachment/'
    COMMENT_TOKEN_VERIFICATION = 'users/auth/verify-ticket-token/'


    static instance;

    constructor() { }

    static getInstance() {
        if (!API.instance) {
            API.instance = new API();
        }
        return API.instance;
    }

    // 🔐 Gestión híbrida de tokens
    getValidToken() {
        // 1. Primero intentar obtener de memoria (más seguro y rápido)
        if (this._accessToken && this._tokenExpiry) {
            const now = Date.now();
            if (now < this._tokenExpiry) {
                console.log('🚀 Token obtenido desde memoria');
                return this._accessToken;
            } else {
                console.log('⚠️ Token en memoria expirado');
                this._clearMemoryTokens();
            }
        }

        // 2. Si no hay en memoria, intentar desde storage (fallback)
        if (this.USE_PERSISTENT_STORAGE) {
            const token = sessionStorage.getItem('access_token');
            const expiry = sessionStorage.getItem('access_token_expiry');
            
            if (token && expiry) {
                const expiryTime = parseInt(expiry);
                const now = Date.now();
                
                if (now < expiryTime) {
                    console.log('💾 Token recuperado desde sessionStorage');
                    // Cargar a memoria para futuras llamadas
                    this._accessToken = token;
                    this._tokenExpiry = expiryTime;
                    return token;
                } else {
                    console.log('⚠️ Token en storage expirado');
                    this._clearStorageTokens();
                }
            }
        }

        console.log('❌ No hay tokens válidos disponibles');
        return null;
    }

    // Guardar solo access token (refresh token está en httpOnly cookie)
    saveAccessToken(accessToken, expiryInMs) {
        const expirationTime = Date.now() + expiryInMs;
        
        // 1. Guardar en memoria (primera prioridad)
        this._accessToken = accessToken;
        this._tokenExpiry = expirationTime;
        
        // 2. Guardar en storage si está habilitado (backup)
        if (this.USE_PERSISTENT_STORAGE) {
            sessionStorage.setItem('access_token', accessToken);
            sessionStorage.setItem('access_token_expiry', expirationTime.toString());
        }
        
        console.log('✅ Access token guardado en memoria y storage');
    }

    // Limpiar access token de memoria
    _clearMemoryTokens() {
        this._accessToken = null;
        this._tokenExpiry = null;
        console.log('🧹 Access token eliminado de memoria');
    }

    // Limpiar access token de storage
    _clearStorageTokens() {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token_expiry');
        console.log('🧹 Access token eliminado de storage');
    }

    // Limpiar todos los tokens
    clearAllTokens() {
        this._clearMemoryTokens();
        this._clearStorageTokens();
        console.log('🗑️ Todos los tokens eliminados');
    }

    // Delegado al authStore (usa httpOnly cookie)
    async refreshAccessToken() {
        if (this.isRefreshing) {
            // Si ya está refrescando, agregar a la cola
            return new Promise((resolve, reject) => {
                this.failedQueue.push({ resolve, reject });
            });
        }

        this.isRefreshing = true;

        try {
            console.log('🔄 Delegando refresh a authStore...');
            
            // Usar authStore para refrescar (lee desde httpOnly cookie)
            const { useAuthStore } = await import('@/stores/authStore.js');
            const authStore = useAuthStore();
            
            const newAccessToken = await authStore.refreshAccessToken();
            
            // Guardar token en memoria para futuras peticiones
            this.saveAccessToken(newAccessToken, 60 * 60 * 1000); // 60 minutos
            
            console.log('✅ Token refrescado y guardado en API memory');
            
            // Procesar cola de peticiones fallidas con el nuevo token
            this.processQueue(null, newAccessToken);
            
            return newAccessToken;
        } catch (error) {
            console.error('❌ Error en refresh delegado:', error.message);
            
            // Limpiar tokens locales
            this.clearAllTokens();
            
            // Procesar cola con error
            this.processQueue(error, null);
            
            throw error;
        } finally {
            this.isRefreshing = false;
        }
    }

    // Procesar cola de peticiones mientras se refrescaba el token
    processQueue(error, token = null) {
        this.failedQueue.forEach(({ resolve, reject }) => {
            if (error) {
                reject(error);
            } else {
                resolve(token);
            }
        });
        
        this.failedQueue = [];
    }

    // 🎛️ Configuración del modo de almacenamiento
    setStorageMode(useStorage = true) {
        this.USE_PERSISTENT_STORAGE = useStorage;
        console.log(`📱 Modo de almacenamiento: ${useStorage ? 'Memoria + SessionStorage' : 'Solo Memoria'}`);
        
        if (!useStorage) {
            // Si se desactiva storage, mover tokens a memoria únicamente
            this._clearStorageTokens();
        }
    }

    // Obtener información del modo actual
    getStorageInfo() {
        return {
            mode: this.USE_PERSISTENT_STORAGE ? 'hybrid' : 'memory-only',
            hasMemoryTokens: !!this._accessToken,
            hasStorageTokens: !!sessionStorage.getItem('access_token'),
            description: this.USE_PERSISTENT_STORAGE ? 
                'Memoria (rápido) + SessionStorage (persistente)' : 
                'Solo memoria (máxima seguridad)'
        };
    }

    // Preparar headers con autenticación
    async prepareHeaders(additionalHeaders = {}, isFormData = false) {
        const headers = { 
            ...additionalHeaders 
        };

        // Solo establecer Content-Type si NO es FormData
        // El navegador establecerá automáticamente multipart/form-data con el boundary correcto
        if (!isFormData && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        // Agregar CSRF si existe
        const csrfToken = this.getCookieValue('csrftoken');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        // Agregar Authorization si hay token
        const token = this.getValidToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    // Helper para obtener valor de cookie
    getCookieValue(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Métodos para interceptors
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    // Aplicar interceptors de request
    async applyRequestInterceptors(config) {
        let finalConfig = { ...config };
        for (const interceptor of this.requestInterceptors) {
            finalConfig = await interceptor(finalConfig);
        }
        return finalConfig;
    }

    // Aplicar interceptors de response
    async applyResponseInterceptors(response) {
        let finalResponse = response;
        for (const interceptor of this.responseInterceptors) {
            finalResponse = await interceptor(finalResponse);
        }
        return finalResponse;
    }

    // Método auxiliar para manejar respuestas HTTP
    async handleResponse(response, endpoint) {
        // Verificar si la respuesta fue exitosa (status 200-299)
        if (!response.ok) {
            // Crear error personalizado basado en el código de estado
            const errorData = {
                status: response.status,
                statusText: response.statusText,
                endpoint: endpoint,
                timestamp: new Date().toISOString()
            };

            // Intentar obtener más detalles del error desde el body
            try {
                const errorBody = await response.text();
                errorData.body = errorBody;

                // Si es JSON, parsearlo
                try {
                    errorData.details = JSON.parse(errorBody);
                } catch {
                    // Si no es JSON válido, mantener como texto
                }
            } catch {
                // Si no se puede leer el body, continuar sin él
            }

            // Lanzar error específico según el código de estado
            switch (response.status) {
                case 400:
                    throw new Error(`Bad Request (400): ${errorData.statusText} - ${endpoint}`);
                case 401:
                    throw new Error(`Unauthorized (401): ${errorData.statusText} - ${endpoint}`);
                case 403:
                    throw new Error(`Forbidden (403): ${errorData.statusText} - ${endpoint}`);
                case 404:
                    throw new Error(`Not Found (404): ${errorData.statusText} - ${endpoint}`);
                case 422:
                    throw new Error(`Unprocessable Entity (422): ${errorData.statusText} - ${endpoint}`);
                case 500:
                    throw new Error(`Internal Server Error (500): ${errorData.statusText} - ${endpoint}`);
                case 502:
                    throw new Error(`Bad Gateway (502): ${errorData.statusText} - ${endpoint}`);
                case 503:
                    throw new Error(`Service Unavailable (503): ${errorData.statusText} - ${endpoint}`);
                default:
                    throw new Error(`HTTP Error (${response.status}): ${errorData.statusText} - ${endpoint}`);
            }
        }

        // Si la respuesta es exitosa, procesarla
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            return Array.isArray(data) ? data : [data];
        } else {
            return await response.text();
        }
    }

    async get(endpoint, headers = {}, options = {}) {
        return this.makeRequest('GET', endpoint, null, headers, options);
    }

    async post(endpoint, data, headers = {}) {
        return this.makeRequest('POST', endpoint, data, headers);
    }

    // Método unificado para hacer requests con manejo automático de tokens
    async makeRequest(method, endpoint, data = null, additionalHeaders = {}, options = {}) {
        try {
            // Detectar si data es FormData
            const isFormData = data instanceof FormData;
            
            // Preparar headers con autenticación automática
            const headers = await this.prepareHeaders(additionalHeaders, isFormData);

            // Configurar request
            const requestConfig = {
                method,
                credentials: "include",
                headers
            };

            // Add body if applicable POST/PUT/PATCH
            if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
                // Si es FormData, enviarlo tal cual; si no, convertir a JSON
                requestConfig.body = isFormData ? data : JSON.stringify(data);
            }

            // Add signal from options if provided (for request cancellation)
            if (options.signal) {
                requestConfig.signal = options.signal;
            }

            // Agregar timeout si está especificado
            if (options.timeout) {
                const controller = new AbortController();
                setTimeout(() => controller.abort(), options.timeout);
                requestConfig.signal = controller.signal;
            }

            // Hacer la petición
            const response = await fetch(this.API_BASE_URL + endpoint, requestConfig);

            // Si es 401 (token expirado), intentar refresh
            if (response.status === 401 && endpoint !== this.REFRESH_TOKEN && endpoint !== this.TOKEN) {
                console.log('🔄 Token expirado (401), intentando refresh...');
                
                try {
                    // Refresh the access token
                    const newAccessToken = await this.refreshAccessToken();
                    
                    if (!newAccessToken) {
                        throw new Error('No se pudo obtener nuevo access token');
                    }
                    
                    console.log('✅ Token refrescado, reintentando petición original...');
                    
                    // Reintentar la petición original con el nuevo token
                    const newHeaders = await this.prepareHeaders(additionalHeaders, isFormData);
                    const retryConfig = {
                        ...requestConfig,
                        headers: newHeaders
                    };
                    
                    const retryResponse = await fetch(this.API_BASE_URL + endpoint, retryConfig);
                    
                    if (retryResponse.status === 401) {
                        // Still 401 after refresh, something is wrong
                        console.error('❌ Aún 401 después de refresh, sesión inválida');
                        throw new Error('SESSION_INVALID');
                    }
                    
                    return await this.handleResponse(retryResponse, endpoint);
                } catch (refreshError) {
                    console.error('❌ Error en refresh:', refreshError.message);
                    
                    // Clear everything and redirect to login
                    this.clearAllTokens();
                    
                    try {
                        const { useAuthStore } = await import('@/stores/authStore.js');
                        const authStore = useAuthStore();
                        authStore.logout();
                    } catch (storeError) {
                        console.error('⚠️ Error limpiando auth store:', storeError);
                    }
                    
                    // Redirect to login
                    try {
                        const { default: router } = await import('@/plugins/router/index.js');
                        router.push('/login');
                    } catch (routerError) {
                        window.location.href = '/login';
                    }
                    
                    throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
                }
            }

            return await this.handleResponse(response, endpoint);
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout: ${endpoint}`);
            }
            console.error(`Error en ${method} ${endpoint}:`, error);
            throw error;
        }
    }

    async put(endpoint, data, headers = {}) {
        return this.makeRequest('PUT', endpoint, data, headers);
    }

    async patch(endpoint, data, headers = {}) {
        return this.makeRequest('PATCH', endpoint, data, headers);
    }

    async delete(endpoint, headers = {}) {
        return this.makeRequest('DELETE', endpoint, null, headers);
    }

    login() {
        window.location.href = this.API_BASE_URL + this.GOOGLE_LOGIN;
    }

    logout() {
        window.location.href = this.API_BASE_URL + this.GOOGLE_LOGOUT;
    }
}

export default API.getInstance()
