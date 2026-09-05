import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { apiFetch, setCsrfToken } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function DoctorLogin() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const inviteToken = searchParams.get('token') || ''

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
      const res = await apiFetch('/doctor/login', {
        method: 'POST',
        json: { trial_id: trialId, username, password },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Login failed.')
        return
      }

      setCsrfToken(data.csrf_token)

      if (inviteToken) {
        const acceptRes = await apiFetch(`/doctor/invitations/${inviteToken}/accept`, {
          method: 'POST',
        })
        const acceptData = await acceptRes.json()
        if (!acceptRes.ok) {
          setError(acceptData.detail || 'Logged in, but could not accept invitation.')
          navigate('/doctor/home', { replace: true })
          return
        }
      }

      navigate('/doctor/home', { replace: true })
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
        <h1>Doctor Login</h1>

        <div className="setup-card">
          <div className="setup-card__header">
            <span className="setup-badge">Doctor Portal</span>
            <h2>Sign In</h2>
            <p>
              {inviteToken
                ? 'Log in to accept your study invitation.'
                : 'Enter your trial ID and credentials to continue.'}
            </p>
          </div>

          <form className="setup-form" onSubmit={handleLogin} noValidate>
            <div className="field">
              <label htmlFor="doctor-login-trial-id">Trial ID</label>
              <input
                id="doctor-login-trial-id"
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
              <label htmlFor="doctor-login-username">Username</label>
              <input
                id="doctor-login-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>
            <div className="field">
              <label htmlFor="doctor-login-password">Password</label>
              <PasswordInput
                id="doctor-login-password"
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

          <p style={{ marginTop: '16px', fontSize: '13px' }}>
            Received an invitation?{' '}
            <Link to={inviteToken ? `/doctor/signup?token=${encodeURIComponent(inviteToken)}` : '/doctor/signup'}>
              Sign up here
            </Link>
          </p>
        </div>
      </main>
    </>
  )
}

export default DoctorLogin
