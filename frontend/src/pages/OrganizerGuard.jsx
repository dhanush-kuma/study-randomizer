import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

/**
 * Hits /organizer/me to check auth state, then redirects:
 *   authenticated   → /organizer/home
 *   unauthenticated → /organizer/login
 */
function OrganizerGuard() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    apiFetch('/organizer/me')
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json()
          storeCsrfFromResponse(data)
        }
        setDestination(res.ok ? '/organizer/home' : '/organizer/login')
      })
      .catch(() => setDestination('/organizer/login'))
  }, [])

  if (!destination) {
    return (
      <>
        <Header />
        <main className="app">
          <p className="loading">Verifying session…</p>
        </main>
      </>
    )
  }

  return <Navigate to={destination} replace />
}

export default OrganizerGuard
