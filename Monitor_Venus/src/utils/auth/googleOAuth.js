// Helpers for the Google OAuth flow (login + link).
// The `state` query param format is `${redirectUri}|${jsonState}`.

import API from '@/utils/api/api'

const DEFAULT_APP_URL = typeof window !== 'undefined' ? window.location.origin : ''

export const APP_URL = import.meta.env.VITE_APP_URL || DEFAULT_APP_URL

export const GOOGLE_REDIRECT_URI = `${APP_URL}/auth/callback`

export const GOOGLE_DEEP_LINK_REDIRECT_URI = 'com.mtr.online://auth/google/callback'

export function buildGoogleState(payload) {
  return encodeURIComponent(JSON.stringify(payload))
}

export function parseGoogleState(stateParam) {
  if (!stateParam || typeof stateParam !== 'string' || !stateParam.includes('|')) return null
  try {
    return JSON.parse(decodeURIComponent(stateParam.split('|').slice(1).join('|')))
  } catch {
    return null
  }
}

async function ensureCsrfCookie() {
  if (API.getCookieValue('csrftoken')) return
  const response = await fetch(`${API.API_BASE_URL}${API.CSRF_TOKEN}`, {
    method: 'GET',
    credentials: 'include',
  })
  if (!response.ok) throw new Error(`No se pudo preparar CSRF (${response.status}).`)
}

// POST { code } to the link endpoint on behalf of the authenticated user.
// Retries once after refreshing the CSRF cookie if the backend rejects a 403.
export async function postGoogleLinkCode(code) {
  try {
    return await API.post(API.GOOGLE_LINK, { code })
  } catch (e) {
    if (String(e?.message || '').includes('403')) {
      await ensureCsrfCookie()
      return await API.post(API.GOOGLE_LINK, { code })
    }
    throw e
  }
}
