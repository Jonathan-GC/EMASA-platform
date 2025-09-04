class API {
    static instance = null;

    API_VERSION = 'v1/';
    API_BASE_URL = 'http://localhost:8000/api/' + this.API_VERSION;

    // Interceptors básicos
    requestInterceptors = [];
    responseInterceptors = [];

    // Flag para evitar loops de refresh
    isRefreshing = false;
    failedQueue = [];

    // 🔐 SISTEMA HÍBRIDO DE TOKENS
    // Tokens en memoria para máxima seguridad (primera opción)
    _accessToken = null;
    _refreshToken = null;
    _tokenExpiry = null;

    // Configuración de almacenamiento
    USE_PERSISTENT_STORAGE = true; // Cambiar a false para solo memoria

    //====[ENDPOINTS]====
    //----[USERS]----
    USER = 'users/user/'

    //----[SESSION]----
    TOKEN = 'token/'
    REFRESH_TOKEN = 'token/refresh'
    CSRF_TOKEN = 'csrf/'
    LOGOUT = 'logout/';

    //----[ORGANIZATIONS]----
    TENANT = 'organizations/tenant/'
    WORKSPACE = 'organizations/workspace/'
    SUBSCRIPTION = 'organizations/subscription/'

    //----[ROLES]----
    ROLE = 'roles/role/'
    ROLE_PERMISSION = 'roles/role-permission/'
    PERMISSION_KEY = 'roles/permission-key/'
    WORKSPACE_MEMBERSHIP = 'roles/workspace-membership/'

    //----[INFRACSTRUCTURE]----
    DEVICE = 'infrastructure/device/'
    GATEWAY = 'infrastructure/gateway/'
    DEVICE_TYPE = 'infrastructure/device-type/'
    MACHINE = 'infrastructure/machine/'
    APPLICATION = 'infrastructure/application/'
    LOCATION = 'infrastructure/location/'
    DEVICE_PROFILE_TEMPLATE = '/device-profile-template/'

    //----[CHIRPSTACK]----

    DEVICE_PROFILE = 'chirpstack/device-profile/'
    TENANT_USER = 'chirpstack/tenant-user/'
    API_USER = 'chirpstack/api-user/'

    //----[SPECIAL]----
    GEN_OBJECT_PERMISSION_KEY = 'regenerate_permission_keys/'


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

    // Guardar token con sistema híbrido
    saveTokens(accessToken, refreshToken, expiryInMs) {
        const expirationTime = Date.now() + expiryInMs;
        
        // 1. Guardar en memoria (primera prioridad)
        this._accessToken = accessToken;
        this._refreshToken = refreshToken;
        this._tokenExpiry = expirationTime;
        
        // 2. Guardar en storage si está habilitado (backup)
        if (this.USE_PERSISTENT_STORAGE) {
            sessionStorage.setItem('access_token', accessToken);
            sessionStorage.setItem('refresh_token', refreshToken);
            sessionStorage.setItem('access_token_expiry', expirationTime.toString());
        }
        
        console.log('✅ Tokens guardados en memoria y storage');
    }

    // Limpiar tokens de memoria
    _clearMemoryTokens() {
        this._accessToken = null;
        this._refreshToken = null;
        this._tokenExpiry = null;
        console.log('🧹 Tokens eliminados de memoria');
    }

    // Limpiar tokens de storage
    _clearStorageTokens() {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('access_token_expiry');
        console.log('🧹 Tokens eliminados de storage');
    }

    // Limpiar todos los tokens
    clearAllTokens() {
        this._clearMemoryTokens();
        this._clearStorageTokens();
        console.log('🗑️ Todos los tokens eliminados');
    }

    // Refresh del access token con sistema híbrido
    async refreshAccessToken() {
        if (this.isRefreshing) {
            // Si ya está refrescando, agregar a la cola
            return new Promise((resolve, reject) => {
                this.failedQueue.push({ resolve, reject });
            });
        }

        this.isRefreshing = true;

        try {
            console.log('🔄 Refrescando access token...');
            
            // Obtener refresh token (primero de memoria, luego de storage)
            let refreshToken = this._refreshToken;
            if (!refreshToken && this.USE_PERSISTENT_STORAGE) {
                refreshToken = sessionStorage.getItem('refresh_token');
            }
            
            if (!refreshToken) {
                throw new Error('No hay refresh token disponible');
            }
            
            const response = await fetch(this.API_BASE_URL + this.REFRESH_TOKEN, {
                method: 'POST',
                credentials: "include",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh: refreshToken })
            });

            if (!response.ok) {
                throw new Error('Refresh token inválido');
            }

            const data = await response.json();
            const newAccessToken = Array.isArray(data) ? data[0]?.access : data?.access;
            const newRefreshToken = Array.isArray(data) ? data[0]?.refresh : data?.refresh;
            
            if (newAccessToken) {
                // Guardar tokens con sistema híbrido
                const expiryInMs = 60 * 60 * 1000; // 60 minutos
                this.saveTokens(
                    newAccessToken, 
                    newRefreshToken || refreshToken, // Usar nuevo refresh o mantener el actual
                    expiryInMs
                );
                
                console.log('✅ Access token refrescado exitosamente');
                
                // Procesar cola de peticiones fallidas
                this.processQueue(null, newAccessToken);
                
                return newAccessToken;
            } else {
                throw new Error('No se recibió access token en la respuesta');
            }
        } catch (error) {
            console.error('❌ Error refrescando token:', error);
            
            // Limpiar todos los tokens si el refresh falla
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
    async prepareHeaders(additionalHeaders = {}) {
        const headers = { 
            'Content-Type': 'application/json',
            ...additionalHeaders 
        };

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
            // Preparar headers con autenticación automática
            const headers = await this.prepareHeaders(additionalHeaders);

            // Configurar request
            const requestConfig = {
                method,
                credentials: "include",
                headers
            };

            // Agregar body si es POST/PUT/PATCH
            if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
                requestConfig.body = JSON.stringify(data);
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
            if (response.status === 401 && endpoint !== this.REFRESH_TOKEN) {
                console.log('🔄 Token expirado, intentando refresh...');
                
                try {
                    await this.refreshAccessToken();
                    
                    // Reintentar la petición original con el nuevo token
                    const newHeaders = await this.prepareHeaders(additionalHeaders);
                    const retryConfig = { ...requestConfig, headers: newHeaders };
                    
                    const retryResponse = await fetch(this.API_BASE_URL + endpoint, retryConfig);
                    return await this.handleResponse(retryResponse, endpoint);
                } catch (refreshError) {
                    console.error('❌ Error en refresh, redirigiendo a login');
                    // Aquí podrías redirigir al login o emitir un evento
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