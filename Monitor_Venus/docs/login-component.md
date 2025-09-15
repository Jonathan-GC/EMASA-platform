# 🔐 Componente de Login - Prueba de Cookies y CSRF

## 📁 Archivos creados:

- **`src/components/LoginForm.vue`** - Componente principal de login con CSRF
- **`src/views/login/index.vue`** - Vista para probar el componente
- **Actualizaciones en `src/utils/api/api.js`** - Mejorado para cookies

## 🎯 Endpoints utilizados:

```javascript
// Desde api.js
TOKEN = 'token/'              // Login principal
REFRESH_TOKEN = 'token/refresh' // Refresh del token
CSRF_TOKEN = 'csrf/'           // Obtener token CSRF
```

## 🛡️ **CSRF Token Implementation**:

### **Flujo automático**:
1. **Verificación**: El login verifica si existe `csrftoken` cookie
2. **Obtención automática**: Si no existe, llama a `/api/v1/csrf/` primero
3. **Header injection**: Agrega `X-CSRFToken` header automáticamente
4. **Visual feedback**: Muestra estado del token en tiempo real

### **Headers enviados**:
```javascript
{
  'Content-Type': 'application/json',
  'X-CSRFToken': 'valor_de_la_cookie_csrftoken'
}
```

## 🍪 Cookies que se crean:

- **`csrftoken`** - Token CSRF para protección ✅
- **`refresh_token`** - Token para refrescar la sesión
- **`sessionid`** - ID de sesión del usuario
- **`access_token`** - Token de acceso (posible)

## 🚀 Funcionalidades del componente:

### ✅ **CSRF Token Management**:
- **Estado visual** - Muestra si el token existe o no
- **Obtención automática** - Se obtiene antes del login si no existe
- **Inyección automática** - Se agrega al header `X-CSRFToken`
- **Actualización en tiempo real** - El estado se actualiza automáticamente

### ✅ **Login**:
- Formulario con usuario y contraseña
- **CSRF automático**: Obtiene token si no existe
- Envía POST a `/api/v1/token/` con `X-CSRFToken` header
- Establece cookies automáticamente

### ✅ **Refresh Token**:
- Botón para refrescar el token
- **Incluye CSRF**: Envía `X-CSRFToken` header
- Envía POST a `/api/v1/token/refresh`
- Usa cookies existentes

### ✅ **CSRF Token Manual**:
- Botón para obtener token CSRF manualmente
- Envía GET a `/api/v1/csrf/`
- Establece cookie `csrftoken`

### ✅ **Ver Cookies**:
- Muestra todas las cookies relevantes
- Formato JSON legible
- Se actualiza automáticamente

### ✅ **Logout**:
- Limpia todas las cookies
- Resetea el formulario
- Limpia el estado

## 🔧 Cómo usar:

1. **Navega a la vista de login**:
   ```
   http://localhost:5177/login
   ```

2. **Observa el estado del CSRF**:
   - ❌ "Token CSRF no encontrado" (inicial)
   - ✅ "Token CSRF disponible" (después de obtenerlo)

3. **Flujo recomendado**:
   - **Opción A**: Solo ingresar credenciales y hacer login (automático)
   - **Opción B**: 1. Obtener CSRF → 2. Login → 3. Refresh Token

4. **Prueba las funciones**:
   - Haz login (CSRF automático)
   - Ve las cookies creadas
   - Prueba refresh token (con CSRF)
   - Obtén CSRF token manualmente
   - Cierra sesión

## 🔍 Debugging:

El componente incluye logs detallados en la consola:
- `🛡️ No hay CSRF token, obteniendo uno...`
- `🛡️ CSRF Token agregado al header: abc123...`
- `⚠️ No se encontró CSRF token en las cookies`
- `🔑 Intentando login con:...`
- `✅ Login exitoso:...`
- `🍪 Cookies encontradas:...`

## 🎨 Características UI:

- **Ionic Vue** components
- **Responsive design**
- **Loading states**
- **Error/success messages**
- **CSRF status indicator** - Estado visual del token
- **Cookie visualization**
- **Iconos modulares**
- **Flujo numerado** - Botones numerados para claridad

## 🛠️ Configuración API:

```javascript
// credentials: "include" está configurado en todos los métodos
// Esto permite enviar/recibir cookies automáticamente
API_BASE_URL = 'http://localhost:8000/api/v1/'

// Helper function para CSRF
const getHeadersWithCSRF = (additionalHeaders = {}) => {
  const csrfToken = getCookieValue('csrftoken');
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }
  return headers;
}
```

## 📱 Testing:

Abre las **DevTools** del navegador:
1. **Application tab** → **Cookies** → **localhost:8000**
2. **Network tab** → Ver headers de requests/responses
   - Verifica que `X-CSRFToken` aparece en los headers
3. **Console** → Ver logs del componente

## 🔒 Seguridad:

- **CSRF Protection**: Todos los POST incluyen `X-CSRFToken`
- **Cookie Security**: `credentials: "include"` para cookies seguras
- **Automatic handling**: No necesitas manejar CSRF manualmente

¡Ya puedes probar el login con CSRF automático! 🚀🛡️
