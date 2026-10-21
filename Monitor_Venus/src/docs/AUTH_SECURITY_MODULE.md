# Módulo de Seguridad de Cuenta (Auth Security)

Documentación del frontend para verificación en dos pasos (TOTP / correo /
códigos de recuperación), confianza de dispositivo, gestión de sesiones y el
nivel de seguridad del tenant.

> Contrato verificado contra el backend en el commit `f14ec7e`
> (`fix(auth): align mfa status response, totp activate detail, trust metadata,
> and email suppression`).

## Endpoints consumidos

Todos definidos en `src/utils/api/api.js`.

| Constante | Método | Ruta | Uso |
| --- | --- | --- | --- |
| `OTP_REQUEST` | POST | `users/auth/otp/request/` | Envía / reenvía el código por correo |
| `OTP_VERIFY` | POST | `users/auth/otp/verify/` | Verifica el código e inicia sesión |
| `MFA_STATUS` | GET | `users/auth/mfa/status/` | Estado de MFA del usuario |
| `MFA_TOTP_SETUP` | POST | `users/auth/mfa/totp/setup/` | Genera secreto + URI `otpauth://` |
| `MFA_TOTP_ACTIVATE` | POST | `users/auth/mfa/totp/activate/` | Confirma el código y entrega backup codes |
| `MFA_TOTP_DEACTIVATE` | POST | `users/auth/mfa/totp/deactivate/` | Desactiva TOTP (requiere contraseña) |
| `SESSIONS` | GET | `users/sessions/` | Lista sesiones activas |
| `SESSIONS_REVOKE(id)` | POST | `users/sessions/{id}/revoke/` | Revoca una sesión |
| `SESSIONS_REVOKE_OTHERS` | POST | `users/sessions/revoke_others/` | Revoca todas menos la actual |
| `SESSIONS_TRUST_CURRENT` | POST | `users/sessions/trust_current/` | Marca o desmarca la sesión actual como de confianza |

> Ojo: las sesiones **no** cuelgan de `auth/`. El backend registra el
> `UserSessionViewSet` en el router raíz de `users` como `sessions`, con las
> acciones `@action(detail=True) revoke` y `@action(detail=False) revoke_others`
> (con guion bajo, no con guion).

`POST users/sessions/trust_current/`

Request: `{ trust: true | false }`
Response: `{ device_trusted: true | false }`

- `trust: true` guarda el hash de confianza en la `UserSession` actual y emite la
  cookie `device_trust_token` con el TTL del nivel de seguridad del tenant.
- `trust: false` (o "") limpia el hash y borra la cookie.
- Requiere CSRF: el cliente reutiliza la cookie existente o pide `csrf/` primero.

### Formatos de respuesta

`GET users/auth/mfa/status/`

```json
{
  "totp_active": true,
  "email_active": true,
  "backup_codes_remaining": 8,
  "methods": [
    { "type": "totp", "label": "Authenticator", "active": true },
    { "type": "email", "label": "Correo", "active": true }
  ]
}
```

> Ojo: la respuesta es un **objeto**, no un arreglo. El código defensivo
> (`Array.isArray(response) ? response[0] : response`) se mantiene para tolerar
> el envoltorio de listas de la API.

`POST users/auth/mfa/totp/activate/`

```json
{
  "detail": "Authenticator activado correctamente.",
  "backup_codes": ["A1B2C3D4", "E5F6G7H8", "..."]
}
```

`POST users/auth/otp/verify/`

Request: `{ username, code, method, trust_device }`
Response: `{ access, refresh, device_trusted }`

`trust_device` viaja siempre en `false` desde este frontend: la confianza se
concede después, con `POST users/sessions/trust_current/`. `device_name` ya no se
envía. `device_trusted` siempre llega en `false` por el mismo motivo.

### Desafío 2FA en `POST users/auth/token/`

Cuando el usuario tiene MFA habilitado la respuesta **no** trae `access`. Trae:

```json
{
  "detail": "Se requiere verificación en dos pasos.",
  "available_methods": ["totp", "email"],
  "primary_method": "totp",
  "allow_device_trust": true,
  "device_trust_ttl_days": 30,
  "email": "usuario@ejemplo.com"
}
```

`primary_method` es `email` únicamente cuando el usuario **no** tiene TOTP
activo. Con TOTP activo el backend suprime el envío del correo, por lo que la
UI **nunca** debe intentar "reenviar" un correo esperando un código TOTP.

## Flujo de login

1. `LoginForm.vue` hace `POST users/auth/token/`.
2. Si la respuesta trae `access`, el login es normal (bypass de 2FA).
3. Si no trae `access`, se guarda el contexto con
   `otpStore.setPendingLogin(identifier, password, challenge)` y se navega a la
   ruta de OTP.
4. `OtpForm.vue` presenta únicamente los métodos de `available_methods`.

### `src/stores/otpStore.js`

Mantiene el estado del desafío 2FA:

| Campo | Origen | Notas |
| --- | --- | --- |
| `identifier` | input del login | Se espeja en `sessionStorage` |
| `password` | input del login | **Solo memoria**, nunca se persiste |
| `availableMethods` | `available_methods` | Normalizado a `totp|email|backup_code` |
| `primaryMethod` | `primary_method` | Método preseleccionado |
| `allowDeviceTrust` | `allow_device_trust` | Si el tenant permite confianza |
| `deviceTrustTtlDays` | `device_trust_ttl_days` | Días de la cookie de confianza |
| `email` | `email` | Destino del código por correo |

El contexto (excepto la contraseña) se espeja en `sessionStorage` bajo
`otp_2fa_context`. Esto es necesario porque en la app móvil la WebView puede
descargarse al entrar en background y se perdería el store de Pinia.
`restoreContext()` recupera ese estado; sin `identifier` restaurado el flujo no
puede continuar y `OtpForm` redirige al login.

`clearPendingLogin()` limpia memoria y `sessionStorage`. Se invoca en
`navigateAfterLogin()` — justo antes del `router.replace` — o al volver al
login. No se limpia al recibir la respuesta correcta: `OtpForm` muestra ~600ms
el estado de éxito y, si se limpiara antes, `availableMethods` quedaría vacío y
el selector de método desaparecería a destiempo.

## Verificación adaptativa

`OtpForm.vue` ofrece un selector de método solo si hay más de una opción:

| Método | Longitud | Input | Notas |
| --- | --- | --- | --- |
| `totp` | 6 | numérico | Código de la app de autenticación |
| `email` | 6 | numérico | Enviado por correo |
| `backup_code` | 8 | texto, mayúsculas | Un solo uso |

El código se autoenvía cuando completa la longitud esperada.

### Reenvío

El botón de reenvío **siempre** llama a `OTP_REQUEST`
(`users/auth/otp/request/`), nunca a `OTP_VERIFY`. Como ese endpoint solo
despacha por correo, tras reenviar el método pasa a `email`.

## Confianza de dispositivo

### `src/utils/auth/deviceTrust.js`

La preferencia se guarda en `localStorage` bajo
`trust_device_prompt_dismissed` con tres estados:

| Valor | Significado |
| --- | --- |
| ausente | El usuario no ha decidido → se muestra la pantalla `/trust` |
| `always` | Confiar siempre en este dispositivo |
| `never` | No confiar nunca en este dispositivo |

API del helper:

- `getTrustDevicePreference()` → `'always' | 'never' | null`
- `isTrustPromptDismissed()` → `true` si hay cualquier preferencia
- `setTrustDevicePreference(pref)`
- `resetTrustDevicePreference()` → vuelve a preguntar
- `getCurrentDeviceName()` → p. ej. `Chrome en Windows`, se muestra en la
  pantalla `/trust` comoinformativo

### Pantalla `/trust` (`src/views/auth/trust/index.vue`)

La decisión se toma **después** de validar el código, en una pantalla completa
—no en un modal— y solo cuando el código es correcto.

Orden del flujo:

1. `OtpForm` hace `POST users/auth/otp/verify/` con `trust_device: false`.
2. Si el código es válido se muestra "¡Código verificado!" y se navega a
   `/trust` tras ~600 ms.
3. `/trust` hace `POST users/sessions/trust_current/` con
   `{ trust: true | false }`.
4. Al terminar, se navega al destino final (`/home`, `/tenants` o
   `/tenant-setup`) según `authStore`.

Reglas:

- Solo se muestra si `allow_device_trust === true`.
- No se muestra con `method === 'backup_code'`.
- No se muestra si ya existe preferencia `always` o `never`.
- No se puede descartar: un código inválido nunca llega a esta pantalla, así que
  no hay forma de saltársela. `onBeforeRouteLeave` bloquea la salida salvo hacia
  las rutas ya autenticadas o al login.
- El checkbox "No volver a preguntar" guarda la decisión elegida
  (`always` o `never`), no solo el haber confiado.

### Preferencia `always` sin pasar por la pantalla

Como `OtpForm` siempre envía `trust_device: false`, el backend ya no emite la
cookie `device_trust_token` por su cuenta. Si el usuario tiene preferencia
`always`, `OtpForm` concede la confianza explícitamente con
`POST users/sessions/trust_current/` `{ trust: true }` tras un ingreso exitoso.
Un fallo en esa llamada no bloquea el ingreso: solo se avisa por consola y el
dispositivo simplemente no queda confiado.

### Seguridad por nivel de tenant

`device_trust_ttl_days` viene del backend según `Tenant.security_level`:

| Nivel | TTL de confianza |
| --- | --- |
| `NONE` | 0 (sin confianza) |
| `LOW` | 60 días |
| `MEDIUM` | 30 días |
| `HIGH` | 0 (verificación siempre) |

## Activación de TOTP

`TotpSetupModal.vue` (`components/modals/auth/`):

1. `POST MFA_TOTP_SETUP` → devuelve `secret` y `otpauth_uri`.
2. Render del QR con `qrcode.vue` (`QrcodeVue`) y muestra del secreto manual.
3. El usuario ingresa 6 dígitos → `POST MFA_TOTP_ACTIVATE`.
4. La respuesta entrega los **backup codes**, que se muestran una sola vez en
   `BackupCodesModal.vue`.

`BackupCodesModal.vue` no permite cerrarse sin marcar "Ya guardé mis códigos en
un lugar seguro" (`can-dismiss` + `will-dismiss` bloquean el botón físico del
móvil). Permite copiar todo y descargar un `.txt`.

## Desactivación

`UserSecurityTab.vue` pide la contraseña actual antes de llamar a
`MFA_TOTP_DEACTIVATE`. Al desactivar se eliminan el secreto TOTP y los backup
codes, y el usuario vuelve a depender del código por correo.

## Sesiones activas

`UserSessionsTab.vue` lista `GET SESSIONS` y marca la sesión actual con
`is_current` (el backend la detecta por la cookie de refresh; el cliente envía
`credentials: "include"`).

- La fila de la sesión actual no muestra botón de revocar.
- "Cerrar otras" llama a `SESSIONS_REVOKE_OTHERS`.

La lista de sesiones no cambia la preferencia de confianza guardada en
`localStorage`; para volver a decidir hay que usar **Seguridad → Dispositivo de
confianza → Cambiar**.

## Nivel de seguridad del tenant

Campo `Tenant.security_level` (`NONE | LOW | MEDIUM | HIGH`, default
`MEDIUM`). El `TenantSerializer` usa `fields = "__all__"`, así que se lee y
escribe por `PATCH organizations/tenant/`.

Frontend:

- `src/schemas/formUpdateSchemas.json` → sección `tenant`, campo
  `security_level` de tipo `select` con las opciones en línea.
- `src/components/tables/tenants/TableTenants.vue` → `setInitialData()` incluye
  `security_level` para que el selector muestre el valor actual.

La ruta `/tenants` ya está protegida por `requireRoles` con
`roles: ['root', 'admin']`, por lo que el selector no queda expuesto a otros
roles. La validación real la aplica el backend.

## Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `components/forms/auth/LoginForm.vue` | Detecta el desafío 2FA y guarda el contexto |
| `components/forms/auth/OtpForm.vue` | Verificación adaptativa + bloqueo de reintentos |
| `views/auth/trust/index.vue` | Decisión de confianza de dispositivo (pantalla completa) |
| `components/modals/auth/TotpSetupModal.vue` | QR + activación de TOTP |
| `components/modals/auth/BackupCodesModal.vue` | Muestra única de códigos de recuperación |
| `components/tabs/UserSecurityTab.vue` | Estado de MFA, activar/desactivar, preferencia de confianza |
| `components/tabs/UserSessionsTab.vue` | Listado y revocación de sesiones |
| `stores/otpStore.js` | Estado del desafío 2FA + decisión de confianza pendiente |
| `utils/auth/deviceTrust.js` | Preferencia local de confianza + nombre de dispositivo |

Las pestañas **Seguridad** y **Sesiones** solo se muestran en el perfil propio
(`isOwnProfile`) en `views/users/detail/index.vue`.
