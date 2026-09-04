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

function getCsrfToken() {
  const stored = sessionStorage.getItem(CSRF_STORAGE_KEY)
  if (stored) return stored

  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export async function apiFetch(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const headers = new Headers(options.headers || {})

  if (UNSAFE_METHODS.has(method)) {
    const csrf = getCsrfToken()
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
