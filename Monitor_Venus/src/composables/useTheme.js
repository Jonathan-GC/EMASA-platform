import { computed, ref } from 'vue'

/**
 * Theme preference: 'light' | 'dark' | 'system'
 *
 * Module-level state (singleton) so every component that calls useTheme()
 * shares the same values without needing provide/inject.
 *
 * Applying a mode does three things:
 *   1. toggles `.dark`          -> Tailwind `dark:` variant + our --app-* tokens
 *   2. toggles `.ion-palette-dark` -> @ionic/vue/css/palettes/dark.class.css
 *   3. updates color-scheme     -> native scrollbars, form controls, status bar
 */

const STORAGE_KEY = 'mtr-theme'
const VALID = ['light', 'dark', 'system']
const THEME_COLOR = { light: '#ffffff', dark: '#18181b' }

const preference = ref('system')
const systemPrefersDark = ref(false)

const resolved = computed(() => {
  if (preference.value === 'dark') return 'dark'
  if (preference.value === 'light') return 'light'
  return systemPrefersDark.value ? 'dark' : 'light'
})

let mediaQuery = null
let initialized = false

function syncMetaTag(isDark) {
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', isDark ? THEME_COLOR.dark : THEME_COLOR.light)
}

function applyMode(mode) {
  if (typeof document === 'undefined') return
  const isDark = mode === 'dark'
  const root = document.documentElement

  root.classList.toggle('dark', isDark)
  root.classList.toggle('ion-palette-dark', isDark)
  root.style.colorScheme = isDark ? 'dark' : 'light'

  syncMetaTag(isDark)
}

/**
 * Set the user preference and persist it.
 * Called by the Appearance card.
 */
export function setPreference(value) {
  const next = VALID.includes(value) ? value : 'system'
  preference.value = next
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch (e) {
    // localStorage can throw in private mode / restricted WebViews
    console.warn('⚠️ No se pudo guardar la preferencia de tema:', e.message)
  }
  applyMode(resolved.value)
}

/**
 * Flip between light and dark. `system` resolves to its opposite.
 */
export function toggle() {
  setPreference(resolved.value === 'dark' ? 'light' : 'dark')
}

/**
 * Read the stored preference, watch the OS setting and apply the mode.
 * Safe to call more than once.
 */
export function initTheme() {
  if (initialized || typeof document === 'undefined') return
  initialized = true

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (VALID.includes(stored)) preference.value = stored
  } catch (e) {
    // ignore - fall back to 'system'
  }

  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = mediaQuery.matches

    const onSystemChange = (event) => {
      systemPrefersDark.value = event.matches
      // Only repaint when the user is following the system
      if (preference.value === 'system') applyMode(resolved.value)
    }

    if (mediaQuery.addEventListener) mediaQuery.addEventListener('change', onSystemChange)
    else if (mediaQuery.addListener) mediaQuery.addListener(onSystemChange)
  }

  applyMode(resolved.value)
}

export function useTheme() {
  initTheme()
  return {
    preference,
    resolved,
    systemPrefersDark,
    setPreference,
    toggle,
  }
}

export default useTheme
