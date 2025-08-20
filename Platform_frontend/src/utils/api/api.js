
class API {

    //API_BASE_URL = '/api/';
    API_BASE_URL = 'http://localhost:8080/api/';

    API_VERSION = 'v1/';

    // Interceptors básicos
    requestInterceptors = [];
    responseInterceptors = [];

    //====[ENDPOINTS]====
    //----[USERS]----
    USER = 'users/user/'

    //----[SESSION]----
    TOKEN = 'token/'
    REFRESH_TOKEN = 'token/refresh'

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

    //----[CHIRPSTACK]----
    DEVICE_PROFILE_TEMPLATE = 'chirpstack/device-profile-template/'
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
        try {
            // Agregar timeout opcional
            const controller = new AbortController();
            if (options.timeout) {
                setTimeout(() => controller.abort(), options.timeout);
            }

            const response = await fetch(this.API_BASE_URL + `${endpoint}`, {
                method: 'GET',
                credentials: "include",
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...headers, // Agregar headers personalizados si existen
                },
            });

            return await this.handleResponse(response, endpoint);
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout: ${endpoint}`);
            }
            console.error(`Error fetching ${endpoint}:`, error);
            throw error;
        }
    }


    async post(endpoint, data, headers = {}) {
        try {
            const response = await fetch(this.API_BASE_URL + `${endpoint}`, {
                method: 'POST',
                credentials: "include",
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': ``, // Agregar token de autorización si existe
                    ...headers
                },
                body: JSON.stringify(data)
            });

            return await this.handleResponse(response, endpoint);
        } catch (error) {
            console.error(`Error posting to ${endpoint}:`, error);
            throw error;
        }
    }

    async put(endpoint, data, headers = {}) {
        try {
            const response = await fetch(this.API_BASE_URL + `${endpoint}`, {
                method: 'PUT',
                credentials: "include",
                headers: {
                    'Content-Type': 'application/json',
                    ...headers
                },
                body: JSON.stringify(data)
            });

            return await this.handleResponse(response, endpoint);
        } catch (error) {
            console.error(`Error putting to ${endpoint}:`, error);
            throw error;
        }
    }

    async delete(endpoint, headers = {}) {
        try {
            const response = await fetch(this.API_BASE_URL + `${endpoint}`, {
                method: 'DELETE',
                credentials: "include",
                headers: {
                    ...headers
                },
            });

            // Para DELETE, el status 204 (No Content) es exitoso pero sin body
            if (response.status === 204) {
                return {}; // Retornar objeto vacío para DELETE exitoso
            }

            return await this.handleResponse(response, endpoint);
        } catch (error) {
            console.error(`Error deleting to ${endpoint}:`, error);
            throw error;
        }
    }

    login() {
        window.location.href = this.API_BASE_URL + this.GOOGLE_LOGIN;
    }

    logout() {
        window.location.href = this.API_BASE_URL + this.GOOGLE_LOGOUT;
    }
}

export default API.getInstance()



