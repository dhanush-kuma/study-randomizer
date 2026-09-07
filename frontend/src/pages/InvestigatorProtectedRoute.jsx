import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

/** Verifies investigator session before rendering child routes. */
function InvestigatorProtectedRoute({ children }) {
  const navigate = useNavigate()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    apiFetch('/investigator/me')
      .then(async (res) => {
        if (!res.ok) {
          navigate('/investigator/login', { replace: true })
          return
        }
        const data = await res.json()
        storeCsrfFromResponse(data)
        setReady(true)
      })
      .catch(() => navigate('/investigator/login', { replace: true }))
  }, [navigate])

  if (!ready) {
    return (
      <>
        <Header />
        <main className="app">
          <p className="loading">Verifying session…</p>
        </main>
      </>
    )
  }

  return children
}

export default InvestigatorProtectedRoute
