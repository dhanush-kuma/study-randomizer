import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiFetch, clearCsrfToken, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

function InvestigatorHome() {
  const navigate = useNavigate()
  const [investigator, setInvestigator] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    apiFetch('/investigator/me')
      .then((res) => {
        if (!res.ok) {
          navigate('/investigator/login', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) {
          storeCsrfFromResponse(data)
          setInvestigator(data)
        }
      })
      .catch(() => navigate('/investigator/login', { replace: true }))
  }, [navigate])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await apiFetch('/investigator/logout', { method: 'POST' })
      clearCsrfToken()
    } catch {
      // Ignore network errors on logout
    }
    navigate('/investigator/login', { replace: true })
  }

  return (
    <>
      <Header>
        {investigator && (
          <button
            className="btn-secondary"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        )}
      </Header>

      <main className="app">
        <h1>Investigator Dashboard</h1>

        {!investigator ? (
          <p className="loading">Verifying session…</p>
        ) : (
          <>
            <div className="status-card" style={{ marginBottom: '28px' }}>
              <div className="label">Session Status</div>
              <p className="message">
                Logged in as <strong>{investigator.name || investigator.username}</strong>
                {' '}· Trial ID: <strong>{investigator.trial_id}</strong>
                {' '}· Username: <code>{investigator.username}</code>
              </p>
            </div>

            <div className="section-header">
              <h2 className="section-title">Account</h2>
            </div>

            <div className="setup-card" style={{ marginTop: '16px' }}>
              <div className="setup-card__header">
                <span className="setup-badge">Security</span>
                <h2>Change Password</h2>
                <p>Update the system-generated password to one of your choice.</p>
              </div>
              <div style={{ padding: '16px 20px' }}>
                <Link
                  to="/investigator/change-password"
                  className="btn-primary"
                  style={{ textDecoration: 'none' }}
                >
                  Change Password →
                </Link>
              </div>
            </div>
          </>
        )}
      </main>
    </>
  )
}

export default InvestigatorHome
