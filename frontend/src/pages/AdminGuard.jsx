import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

/**
 * Hits /admin/me to check auth state, then redirects:
 *   authenticated  → /admin/home
 *   unauthenticated → /admin/login
 */
function AdminGuard() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    apiFetch('/admin/me')
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json()
          storeCsrfFromResponse(data)
        }
        setDestination(res.ok ? '/admin/home' : '/admin/login')
      })
      .catch(() => setDestination('/admin/login'))
  }, [])

  if (!destination) {
    return (
      <>
        <Header />
        <main className="app">
          <p className="loading">Checking session…</p>
        </main>
      </>
    )
  }

  return <Navigate to={destination} replace />
}

export default AdminGuard
