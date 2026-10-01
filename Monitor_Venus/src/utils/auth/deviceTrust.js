// Preferencia local sobre el aviso "¿Confiar en este dispositivo?".
// El backend decide si el tenant permite confianza de dispositivo
// (allow_device_trust en la respuesta de POST /token/); aquí solo se
// recuerda la decisión del usuario para no volver a mostrar el aviso.
//
// Valores posibles de la preferencia:
//   null      -> el usuario todavía no ha decidido, se muestra el aviso
//   'always'  -> confiar siempre en este dispositivo
//   'never'   -> nunca confiar en este dispositivo
const TRUST_PROMPT_KEY = 'trust_device_prompt_dismissed';
const TRUST_PREFERENCE_ALWAYS = 'always';
const TRUST_PREFERENCE_NEVER = 'never';

const VALID_PREFERENCES = [TRUST_PREFERENCE_ALWAYS, TRUST_PREFERENCE_NEVER];

/**
 * Devuelve la preferencia guardada: 'always', 'never' o null si no hay.
 */
export const getTrustDevicePreference = () => {
  try {
    const raw = localStorage.getItem(TRUST_PROMPT_KEY);
    return VALID_PREFERENCES.includes(raw) ? raw : null;
  } catch (err) {
    console.warn('No se pudo leer la preferencia de confianza:', err);
    return null;
  }
};

/**
 * true cuando el usuario pidió no volver a ver el aviso,
 * sin importar si confió en el dispositivo o no.
 */
export const isTrustPromptDismissed = () => getTrustDevicePreference() !== null;

/**
 * Persiste la decisión del usuario.
 * @param {'always'|'never'|null} preference
 */
export const setTrustDevicePreference = (preference) => {
  try {
    if (preference === null) {
      localStorage.removeItem(TRUST_PROMPT_KEY);
      return;
    }
    localStorage.setItem(TRUST_PROMPT_KEY, preference);
  } catch (err) {
    console.warn('No se pudo guardar la preferencia de confianza:', err);
  }
};

/**
 * Permite volver a preguntar al usuario (usado por la pestaña de Seguridad).
 */
export const resetTrustDevicePreference = () => setTrustDevicePreference(null);

/**
 * Nombre legible del dispositivo actual, usado en el payload `device_name`
 * que el backend persiste en UserSession.device_name.
 * El backend genera uno desde el User-Agent si no se envía, pero enviarlo
 * permite que el usuario distinga sus dispositivos.
 */
export const getCurrentDeviceName = () => {
  if (typeof navigator === 'undefined') return 'Navegador web';

  const ua = navigator.userAgent || '';
  const source = navigator.userAgentData;

  let os = 'desconocido';
  let browser = 'Navegador';

  if (source && Array.isArray(source.platform)) {
    os = source.platform;
  } else if (/Windows/i.test(ua)) os = 'Windows';
  else if (/iPhone|iPad|iPod/i.test(ua)) os = 'iOS';
  else if (/Android/i.test(ua)) os = 'Android';
  else if (/Mac OS X|Macintosh/i.test(ua)) os = 'macOS';
  else if (/Linux/i.test(ua)) os = 'Linux';

  if (/Edg\//i.test(ua)) browser = 'Edge';
  else if (/OPR\//i.test(ua)) browser = 'Opera';
  else if (/Chrome\//i.test(ua)) browser = 'Chrome';
  else if (/Safari\//i.test(ua)) browser = 'Safari';
  else if (/Firefox\//i.test(ua)) browser = 'Firefox';

  return `${browser} en ${os}`;
};
