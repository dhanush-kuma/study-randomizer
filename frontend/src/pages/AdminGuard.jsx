import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { API_URL } from '../config'

/**
 * Hits /admin/me to check auth state, then redirects:
 *   authenticated  → /admin/home
 *   unauthenticated → /admin/login
 */
function AdminGuard() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/admin/me`, { credentials: 'include' })
      .then((res) => {
        setDestination(res.ok ? '/admin/home' : '/admin/login')
      })
      .catch(() => setDestination('/admin/login'))
  }, [])

  if (!destination) {
    return (
      <>
        <header className="app-header">
          <span className="site-name">Study Randomizer</span>
        </header>
        <main className="app">
          <p className="loading">Checking session…</p>
        </main>
      </>
    )
  }

  return <Navigate to={destination} replace />
}

export default AdminGuard
