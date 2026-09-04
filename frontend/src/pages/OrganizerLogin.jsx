import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, setCsrfToken } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function OrganizerLogin() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const res = await apiFetch('/organizer/login', {
        method: 'POST',
        json: { username, password },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Login failed.')
        return
      }

      setCsrfToken(data.csrf_token)
      navigate('/organizer/home', { replace: true })
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
        <h1>Organizer Portal</h1>

        <div className="setup-card">
          <div className="setup-card__header">
            <span className="setup-badge">Organizer Area</span>
            <h2>Organizer Sign In</h2>
            <p>Enter your organizer credentials to log in to the randomizer.</p>
          </div>

          <form className="setup-form" onSubmit={handleLogin} noValidate>
            <div className="field">
              <label htmlFor="org-username">Username</label>
              <input
                id="org-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="organizer"
                required
                autoComplete="username"
                autoFocus
              />
            </div>

            <div className="field">
              <label htmlFor="org-password">Password</label>
              <PasswordInput
                id="org-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                autoComplete="current-password"
              />
            </div>

            {error && <p className="error">{error}</p>}

            <button
              id="btn-org-login"
              type="submit"
              className="btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Authenticating…' : 'Sign In'}
            </button>
          </form>
        </div>
      </main>
    </>
  )
}

export default OrganizerLogin
