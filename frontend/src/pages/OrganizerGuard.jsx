import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { API_URL } from '../config'
import Header from '../components/Header'

/**
 * Hits /organizer/me to check auth state, then redirects:
 *   authenticated   → /organizer/home
 *   unauthenticated → /organizer/login
 */
function OrganizerGuard() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/organizer/me`, { credentials: 'include' })
      .then((res) => {
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
