import { API_URL } from './config'

const CSRF_STORAGE_KEY = 'csrf_token'
const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

export function setCsrfToken(token) {
  if (token) {
    sessionStorage.setItem(CSRF_STORAGE_KEY, token)
  }
}

export function clearCsrfToken() {
  sessionStorage.removeItem(CSRF_STORAGE_KEY)
}

export function storeCsrfFromResponse(data) {
  if (data?.csrf_token) setCsrfToken(data.csrf_token)
}

function getCsrfToken() {
  const stored = sessionStorage.getItem(CSRF_STORAGE_KEY)
  if (stored) return stored

  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

function mePathForApiPath(path) {
  if (path.startsWith('/organizer')) return '/organizer/me'
  if (path.startsWith('/admin')) return '/admin/me'
  if (path.startsWith('/investigator')) return '/investigator/me'
  return null
}

/** Fetch a fresh CSRF token when sessionStorage is empty (cross-origin dev). */
async function bootstrapCsrfIfNeeded(apiPath) {
  const existing = getCsrfToken()
  if (existing) return existing

  const mePath = mePathForApiPath(apiPath)
  if (!mePath) return ''

  const res = await fetch(`${API_URL}${mePath}`, { credentials: 'include' })
  if (!res.ok) return ''

  const data = await res.json()
  storeCsrfFromResponse(data)
  return data.csrf_token || ''
}

export async function apiFetch(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})

  if (UNSAFE_METHODS.has(method)) {
    const csrf = await bootstrapCsrfIfNeeded(path)
    if (csrf) headers.set('X-CSRF-Token', csrf)
  }

  if (options.json !== undefined) {
    headers.set('Content-Type', 'application/json')
    options.body = JSON.stringify(options.json)
    delete options.json
  }

  if (options.setupToken) {
    headers.set('X-Setup-Token', options.setupToken)
    delete options.setupToken
  }

  return fetch(`${API_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
  })
}
