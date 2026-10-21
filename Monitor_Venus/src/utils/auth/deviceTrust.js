import { Capacitor } from '@capacitor/core';

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

// ---------------------------------------------------------------------------
// Detección de dispositivo a partir del User-Agent
// ---------------------------------------------------------------------------

// Orden importante: Android debe ir antes que Linux (los UAs de Android
// incluyen "Linux") y iOS antes que macOS.
const OS_PATTERNS = [
  ['android', /Android/i],
  ['ios', /iPhone|iPad|iPod/i],
  ['windows', /Windows/i],
  ['macos', /Mac OS X|Macintosh/i],
  ['linux', /Linux|X11/i],
];

// Orden importante: los UAs de Chromium incluyen "Chrome" y "Safari"; el
// de Edge incluye los tres ("Chrome", "Safari" y "Edg") y el Edge clásico
// (EdgeHTML) incluye "Chrome" y "Edge/". Por eso Edge clásico se prueba
// primero y Safari al final.
const BROWSER_PATTERNS = [
  ['edge-legacy', /Edge\//i], // EdgeHTML, anterior a Chromium
  ['edge', /Edg(A|iOS)?\//i], // Edg/ escritorio, EdgA/ Android, EdgiOS/
  ['opera', /OPR\/|Opera/i],
  ['samsung', /SamsungBrowser\//i],
  ['internet-explorer', /MSIE |Trident\//i],
  ['firefox', /Firefox\/|FxiOS\//i],
  ['chrome', /Chrome\/|CriOS\//i],
  ['safari', /Safari\//i],
];

const OS_DISPLAY_NAMES = {
  windows: 'Windows',
  ios: 'iOS',
  android: 'Android',
  macos: 'macOS',
  linux: 'Linux',
};

const BROWSER_DISPLAY_NAMES = {
  'edge-legacy': 'Edge clásico',
  edge: 'Edge',
  opera: 'Opera',
  samsung: 'Samsung Internet',
  'internet-explorer': 'Internet Explorer',
  firefox: 'Firefox',
  chrome: 'Chrome',
  safari: 'Safari',
};

/**
 * Detecta SO, navegador, tipo de dispositivo y si el UA corresponde a la
 * app nativa (WebView) desde un User-Agent.
 * Devuelve { os, browser, deviceType, native } con null cuando no se detecta.
 *   os:         'android' | 'ios' | 'macos' | 'windows' | 'linux' | null
 *   browser:    'chrome' | 'firefox' | 'edge' | 'edge-legacy' |
 *               'internet-explorer' | 'safari' | 'opera' | 'samsung' | null
 *   deviceType: 'mobile' | 'tablet' | 'desktop' | null
 *   native:     'android' | 'ios' | null
 */
export const parseUserAgent = (ua) => {
  if (!ua || typeof ua !== 'string') {
    return { os: null, browser: null, deviceType: null, native: null };
  }

  const os = (OS_PATTERNS.find(([, re]) => re.test(ua)) || [null])[0];
  const browser = (BROWSER_PATTERNS.find(([, re]) => re.test(ua)) || [null])[0];

  // Android con "Mobile" es teléfono; sin "Mobile" suele ser tablet.
  let deviceType = null;
  if (/iPad|Tablet|PlayBook|Silk/i.test(ua)) deviceType = 'tablet';
  else if (/Mobi|iPhone|Windows Phone|IEMobile/i.test(ua)) deviceType = 'mobile';
  else if (/Android/i.test(ua)) deviceType = 'tablet';
  else deviceType = 'desktop';

  // App nativa (Capacitor) por heurística del UA:
  // - Android: el WebView añade el marcador "; wv)". Ese UA también
  //   contiene "Chrome/", por eso `native` se resuelve antes que el
  //   navegador al elegir el icono.
  // - iOS: el WKWebView incluye "Mobile/" pero no el token "Safari/" ni
  //   tokens de navegadores de terceros (también aplica a webviews de
  //   otras apps, p. ej. Facebook/Instagram, que también son contextos
  //   de app nativa).
  let native = null;
  if (/;\s*wv[;)]/i.test(ua)) {
    native = 'android';
  } else if (
    /AppleWebKit/i.test(ua) &&
    /Mobile\//i.test(ua) &&
    !/Safari\/|CriOS|FxiOS|EdgiOS|EdgA|OPR\/|SamsungBrowser\//i.test(ua)
  ) {
    native = 'ios';
  }

  return { os, browser, deviceType, native };
};

/**
 * Info del dispositivo actual (navigator + Capacitor). En la app nativa
 * la detección exacta la da Capacitor; fuera de ella se usa el User-Agent,
 * con userAgentData.platform (Chromium) como respaldo si no revela el SO.
 */
export const getCurrentDeviceInfo = () => {
  if (typeof navigator === 'undefined') {
    return { os: null, browser: null, deviceType: null, native: null, userAgent: '' };
  }

  const ua = navigator.userAgent || '';
  const info = parseUserAgent(ua);

  // En la app nativa el veredicto de Capacitor prevalece sobre la
  // heurística del UA (el WebView puede no traer marcadores propios).
  if (Capacitor.isNativePlatform()) {
    const platform = Capacitor.getPlatform(); // 'android' | 'ios'
    if (platform === 'android' || platform === 'ios') info.native = platform;
  }

  // userAgentData.platform es un string ("Windows", "macOS", "Android", ...)
  const source = navigator.userAgentData;
  if (!info.os && source && typeof source.platform === 'string') {
    const platform = source.platform.toLowerCase();
    if (platform.includes('win')) info.os = 'windows';
    else if (platform.includes('android')) info.os = 'android';
    else if (platform.includes('mac')) info.os = 'macos';
    else if (platform.includes('linux')) info.os = 'linux';
  }

  return { ...info, userAgent: ua };
};

/**
 * Nombre legible del dispositivo actual, usado en el payload `device_name`
 * que el backend persiste en UserSession.device_name.
 * El backend genera uno desde el User-Agent si no se envía, pero enviarlo
 * permite que el usuario distinga sus dispositivos.
 */
export const getCurrentDeviceName = () => {
  if (typeof navigator === 'undefined') return 'Navegador web';

  const { os, browser, native } = getCurrentDeviceInfo();

  // La app nativa se nombra explícitamente: el UA del WebView arrastra
  // tokens de Chrome/Safari que resultarían engañosos en la lista.
  if (native === 'android') return 'Monitor Android';
  if (native === 'ios') return 'Monitor iOS';

  const osName = OS_DISPLAY_NAMES[os] || 'desconocido';
  const browserName = BROWSER_DISPLAY_NAMES[browser] || 'Navegador';

  return `${browserName} en ${osName}`;
};
