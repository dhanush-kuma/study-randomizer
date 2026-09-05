import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, setCsrfToken } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function InvestigatorLogin() {
  const navigate = useNavigate()

  const [trialId, setTrialId] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const res = await apiFetch('/investigator/login', {
        method: 'POST',
        json: {
          trial_id: trialId.trim(),
          username: username.trim(),
          password,
        },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Login failed.')
        return
      }

      setCsrfToken(data.csrf_token)
      navigate('/investigator/home', { replace: true })
    } catch {
      setError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Header />

      <main className="app">
        <h1>Investigator Login</h1>

        <div className="setup-card">
          <div className="setup-card__header">
            <span className="setup-badge">Investigator Portal</span>
            <h2>Sign In</h2>
            <p>Enter your trial ID, username, and password to continue.</p>
          </div>

          <form className="setup-form" onSubmit={handleLogin} noValidate>
            <div className="field">
              <label htmlFor="inv-login-trial-id">Trial ID</label>
              <input
                id="inv-login-trial-id"
                type="text"
                value={trialId}
                onChange={(e) => setTrialId(e.target.value)}
                placeholder="Protocol code (e.g. TRL-2024-001)"
                required
                autoFocus
                autoComplete="off"
              />
            </div>
            <div className="field">
              <label htmlFor="inv-login-username">Username</label>
              <input
                id="inv-login-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. 000001"
                required
                autoComplete="username"
              />
            </div>
            <div className="field">
              <label htmlFor="inv-login-password">Password</label>
              <PasswordInput
                id="inv-login-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            {error && <p className="error">{error}</p>}
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        </div>
      </main>
    </>
  )
}

export default InvestigatorLogin
