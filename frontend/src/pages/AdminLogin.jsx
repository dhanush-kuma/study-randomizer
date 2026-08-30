import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_URL } from '../config'

function AdminLogin() {
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
      const res = await fetch(`${API_URL}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',        // needed for the cookie to be set
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Login failed.')
        return
      }

      navigate('/admin/home', { replace: true })
    } catch {
      setError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <header className="app-header">
        <span className="site-name">Study Randomizer</span>
      </header>

      <main className="app">
        <h1>Admin Login</h1>

        <div className="setup-card">
          <div className="setup-card__header">
            <span className="setup-badge">Admin Area</span>
            <h2>Sign In</h2>
            <p>Enter your admin credentials to continue.</p>
          </div>

          <form className="setup-form" onSubmit={handleLogin} noValidate>
            <div className="field">
              <label htmlFor="admin-username">Username</label>
              <input
                id="admin-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                autoComplete="username"
                autoFocus
              />
            </div>

            <div className="field">
              <label htmlFor="admin-password">Password</label>
              <input
                id="admin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                autoComplete="current-password"
              />
            </div>

            {error && <p className="error">{error}</p>}

            <button
              id="btn-admin-login"
              type="submit"
              className="btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        </div>
      </main>
    </>
  )
}

export default AdminLogin
