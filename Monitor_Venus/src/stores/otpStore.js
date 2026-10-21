// OTP Store - Guarda temporalmente las credenciales del login pendiente
// La contraseña SOLO vive en memoria (nunca se persiste). El resto del
// contexto 2FA se espeja en sessionStorage para sobrevivir a que la app
// móvil entre en background durante el flujo (el store Pinia se pierde al
// recargar la WebView). Todo se limpia al verificar o al salir del flujo.
import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

const CONTEXT_KEY = 'otp_2fa_context';

// Clave propia para la pantalla de confianza: se escribe justo después de
// verificar el código y se borra al tomar la decisión (o al navegar).
const TRUST_KEY = 'otp_trust_decision';

// Métodos soportados por el backend (OTPVerifySerializer.validate_method)
const KNOWN_METHODS = ['totp', 'email', 'backup_code'];

const normalizeMethods = (value) => {
  const list = Array.isArray(value) ? value : [];
  return list.filter(m => KNOWN_METHODS.includes(m));
};

// El contexto de métodos se espeja en sessionStorage para sobrevivir a que
// la app móvil entre en background durante el flujo 2FA (el store Pinia se
// pierde al recargar la WebView).
const readPersistedContext = () => {
  try {
    const raw = sessionStorage.getItem(CONTEXT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return {
      identifier: typeof parsed.identifier === 'string' ? parsed.identifier : null,
      availableMethods: normalizeMethods(parsed.availableMethods),
      primaryMethod: KNOWN_METHODS.includes(parsed.primaryMethod) ? parsed.primaryMethod : null,
      allowDeviceTrust: parsed.allowDeviceTrust !== false,
      deviceTrustTtlDays: Number.isFinite(parsed.deviceTrustTtlDays) ? parsed.deviceTrustTtlDays : 30,
      email: typeof parsed.email === 'string' ? parsed.email : null
    };
  } catch (err) {
    console.warn('No se pudo leer el contexto 2FA persistido:', err);
    return null;
  }
};

const clearPersistedContext = () => {
  try {
    sessionStorage.removeItem(CONTEXT_KEY);
  } catch (err) {
    console.warn('No se pudo limpiar el contexto 2FA persistido:', err);
  }
};

// La decisión de confianza se guarda aparte porque en ese punto el contexto 2FA
// ya fue validado: si la WebView móvil se recarga, la pantalla de confianza debe
// poder seguirse mostrando en lugar de expulsar al usuario al login.
const readPersistedTrust = () => {
  try {
    const raw = sessionStorage.getItem(TRUST_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return {
      deviceTrustTtlDays: Number.isFinite(parsed.deviceTrustTtlDays) ? parsed.deviceTrustTtlDays : 30
    };
  } catch (err) {
    console.warn('No se pudo leer la decisión de confianza persistida:', err);
    return null;
  }
};

const clearPersistedTrust = () => {
  try {
    sessionStorage.removeItem(TRUST_KEY);
  } catch (err) {
    console.warn('No se pudo limpiar la decisión de confianza persistida:', err);
  }
};

export const useOtpStore = defineStore('otp', () => {
  // Identificador usado para la verificación (email o username)
  const identifier = ref(null);
  // Contraseña en memoria, necesaria solo para reenviar el código
  const password = ref(null);

  // Métodos de 2FA habilitados para este login (respuesta de POST /token/)
  const availableMethods = ref([]);
  // Método preferido por el backend (totp | email)
  const primaryMethod = ref(null);
  // El tenant permite emitir la cookie device_trust_token
  const allowDeviceTrust = ref(true);
  // Días de validez de la cookie de confianza (viene del backend)
  const deviceTrustTtlDays = ref(30);
  // Email del usuario (para mostrar a dónde se envió el código)
  const email = ref(null);
  // El código OTP ya fue verificado y falta decidir si se confía en el
  // dispositivo. La pantalla /trust es obligatoria y no se puede saltar.
  const trustDecisionRequired = ref(false);

  const restoreContext = () => {
    const ctx = readPersistedContext();
    if (ctx) {
      // La contraseña NUNCA se persiste: solo en memoria.
      identifier.value = ctx.identifier || identifier.value;
      availableMethods.value = ctx.availableMethods;
      primaryMethod.value = ctx.primaryMethod;
      allowDeviceTrust.value = ctx.allowDeviceTrust;
      deviceTrustTtlDays.value = ctx.deviceTrustTtlDays;
      email.value = ctx.email;
    }
    return ctx;
  };

  /**
   * Marca que el código OTP fue verificado y que se debe pedir la decisión
   * de confianza antes de continuar al inicio de sesión.
   */
  const requireTrustDecision = () => {
    trustDecisionRequired.value = true;
    try {
      sessionStorage.setItem(
        TRUST_KEY,
        JSON.stringify({ deviceTrustTtlDays: deviceTrustTtlDays.value })
      );
    } catch (err) {
      console.warn('No se pudo persistir la decisión de confianza:', err);
    }
  };

  /**
   * Recupera el flag de decisión de confianza tras una recarga de la WebView.
   * @returns {boolean} true si hay una decisión pendiente
   */
  const restoreTrustDecision = () => {
    const ctx = readPersistedTrust();
    if (!ctx) return false;
    trustDecisionRequired.value = true;
    if (Number.isFinite(ctx.deviceTrustTtlDays)) {
      deviceTrustTtlDays.value = ctx.deviceTrustTtlDays;
    }
    return true;
  };

  /**
   * Marca la decisión de confianza como resuelta.
   */
  const clearTrustDecision = () => {
    trustDecisionRequired.value = false;
    clearPersistedTrust();
  };

  /**
   * Guarda el login pendiente de verificar por OTP
   * @param {string} loginIdentifier - Email o username ingresado
   * @param {string} loginPassword - Contraseña (solo memoria)
   * @param {object} challenge - Contexto 2FA devuelto por POST /token/
   */
  const setPendingLogin = (loginIdentifier, loginPassword, challenge = {}) => {
    identifier.value = loginIdentifier || null;
    password.value = loginPassword || null;

    availableMethods.value = normalizeMethods(challenge.available_methods);
    primaryMethod.value = KNOWN_METHODS.includes(challenge.primary_method)
      ? challenge.primary_method
      : (availableMethods.value[0] || 'email');
    allowDeviceTrust.value = challenge.allow_device_trust !== false;
    deviceTrustTtlDays.value = Number.isFinite(challenge.device_trust_ttl_days)
      ? challenge.device_trust_ttl_days
      : 30;
    email.value = challenge.email || null;

    // Sin métodos informados, el backend solo garantiza el código por correo
    if (availableMethods.value.length === 0) {
      availableMethods.value = ['email'];
    }
  };

  /**
   * Limpia el login pendiente (al verificar o cancelar)
   */
  const clearPendingLogin = () => {
    identifier.value = null;
    password.value = null;
    availableMethods.value = [];
    primaryMethod.value = null;
    allowDeviceTrust.value = true;
    deviceTrustTtlDays.value = 30;
    email.value = null;
    clearPersistedContext();
    clearTrustDecision();
  };

  // Espeja el contexto 2FA en sessionStorage
  watch(
    [identifier, availableMethods, primaryMethod, allowDeviceTrust, deviceTrustTtlDays, email],
    () => {
      if (!identifier.value) return;
      try {
        sessionStorage.setItem(CONTEXT_KEY, JSON.stringify({
          identifier: identifier.value,
          availableMethods: availableMethods.value,
          primaryMethod: primaryMethod.value,
          allowDeviceTrust: allowDeviceTrust.value,
          deviceTrustTtlDays: deviceTrustTtlDays.value,
          email: email.value
        }));
      } catch (err) {
        console.warn('No se pudo persistir el contexto 2FA:', err);
      }
    },
    { deep: true }
  );

  return {
    identifier,
    password,
    availableMethods,
    primaryMethod,
    allowDeviceTrust,
    deviceTrustTtlDays,
    email,
    trustDecisionRequired,
    restoreContext,
    setPendingLogin,
    clearPendingLogin,
    requireTrustDecision,
    restoreTrustDecision,
    clearTrustDecision
  };
});
