// Resolución del icono de dispositivo/navegador para la lista de sesiones
// y el aviso de dispositivo de confianza.
//
// Devuelve claves del registro de iconos (src/plugins/icons/icons.js), no
// los iconos en sí, para mantener este módulo desacoplado del plugin.
// Los logos de marca son los de Font Awesome (@fortawesome/fontawesome-free).
//
// Prioridad (un solo icono):
//   1. App nativa (Capacitor)  -> logo de la plataforma
//   2. Navegador conocido      -> logo del navegador
//   3. SO conocido             -> logo de la plataforma (respaldo para
//                                 navegadores sin logo en FA, p. ej.
//                                 Samsung Internet)
//   4. Tipo de dispositivo     -> icono genérico (teléfono/tablet/escritorio)
//   5. Desconocido total       -> globo

import { parseUserAgent } from './deviceTrust.js';

// SO / plataforma detectada -> logo de marca del registro de iconos
export const OS_ICON_KEYS = {
  android: 'fa_android',
  ios: 'fa_apple',
  macos: 'fa_apple',
  windows: 'fa_windows',
  linux: 'fa_linux',
};

// Navegador detectado -> logo de marca. Opera, Internet Explorer y el Edge
// clásico tienen logo en Font Awesome (ionicons no los tenía). Samsung
// Internet no existe en FA: queda fuera y cae al logo de plataforma.
export const BROWSER_ICON_KEYS = {
  chrome: 'fa_chrome',
  firefox: 'fa_firefox',
  edge: 'fa_edge',
  'edge-legacy': 'fa_edge_legacy',
  safari: 'fa_safari',
  opera: 'fa_opera',
  'internet-explorer': 'fa_internet_explorer',
};

// Tipo de dispositivo -> icono genérico de hardware (ionicons)
export const DEVICE_TYPE_ICON_KEYS = {
  mobile: 'phone_portrait',
  tablet: 'tablet',
  desktop: 'desktop',
};

// Respaldos sobre el nombre legible (el backend lo genera desde el UA
// cuando el cliente no envía device_name, p. ej. "Chrome en Linux").
const OS_NAME_FALLBACKS = [
  [/android/, 'android'],
  [/iphone|ipad|ios/, 'ios'],
  [/windows/, 'windows'],
  [/mac/, 'macos'],
  [/linux/, 'linux'],
];

const BROWSER_NAME_FALLBACKS = [
  [/edge legacy|edge clásico/, 'edge-legacy'],
  [/edge/, 'edge'],
  [/opera/, 'opera'],
  [/internet explorer/, 'internet-explorer'],
  [/firefox/, 'firefox'],
  [/chrome/, 'chrome'],
  [/safari/, 'safari'],
  [/samsung/, 'samsung'],
];

// Nombres con los que getCurrentDeviceName() identifica la app nativa.
const NATIVE_NAME_FALLBACKS = [
  [/monitor\s+android/, 'android'],
  [/monitor\s+ios/, 'ios'],
];

/**
 * Detecta SO/navegador/tipo/app-nativa a partir del User-Agent de una
 * sesión, con respaldo sobre el nombre legible del dispositivo si el UA
 * no dice nada.
 * @param {{ userAgent?: string, deviceName?: string }} source
 * @returns {{ os: string|null, browser: string|null, deviceType: string|null, native: string|null }}
 */
export const resolveDeviceInfo = ({ userAgent, deviceName } = {}) => {
  const info = parseUserAgent(userAgent);
  const name = String(deviceName || '').toLowerCase();

  if (!info.native && name) {
    const hit = NATIVE_NAME_FALLBACKS.find(([re]) => re.test(name));
    if (hit) info.native = hit[1];
  }

  if (!info.os && name) {
    const hit = OS_NAME_FALLBACKS.find(([re]) => re.test(name));
    if (hit) info.os = hit[1];
  }

  if (!info.browser && name) {
    const hit = BROWSER_NAME_FALLBACKS.find(([re]) => re.test(name));
    if (hit) info.browser = hit[1];
  }

  return info;
};

/**
 * Traduce info semántica de dispositivo a la clave del icono a mostrar.
 * @param {{ os?: string|null, browser?: string|null, deviceType?: string|null, native?: string|null }} info
 * @returns {string} clave del registro de iconos
 */
export const getDeviceIconKey = ({ os, browser, deviceType, native } = {}) => {
  if (native) return OS_ICON_KEYS[native] || 'globe';
  if (browser && BROWSER_ICON_KEYS[browser]) return BROWSER_ICON_KEYS[browser];
  if (os && OS_ICON_KEYS[os]) return OS_ICON_KEYS[os];
  if (deviceType) return DEVICE_TYPE_ICON_KEYS[deviceType];
  return 'globe';
};
