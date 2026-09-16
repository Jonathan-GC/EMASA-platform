// OTP Store - Guarda temporalmente las credenciales del login pendiente
// SOLO vive en memoria (no se persiste en localStorage) y se limpia al
// completar la verificación OTP o al salir del flujo.
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useOtpStore = defineStore('otp', () => {
  // Identificador usado para la verificación (email o username)
  const identifier = ref(null);
  // Contraseña en memoria, necesaria solo para reenviar el código
  const password = ref(null);

  /**
   * Guarda el login pendiente de verificar por OTP
   * @param {string} loginIdentifier - Email o username ingresado
   * @param {string} loginPassword - Contraseña (solo memoria)
   */
  const setPendingLogin = (loginIdentifier, loginPassword) => {
    identifier.value = loginIdentifier || null;
    password.value = loginPassword || null;
  };

  /**
   * Limpia el login pendiente (al verificar o cancelar)
   */
  const clearPendingLogin = () => {
    identifier.value = null;
    password.value = null;
  };

  return {
    identifier,
    password,
    setPendingLogin,
    clearPendingLogin
  };
});
