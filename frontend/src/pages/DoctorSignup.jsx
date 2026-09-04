import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { apiFetch, setCsrfToken } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function DoctorSignup() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''

  const [preview, setPreview] = useState(null)
  const [phase, setPhase] = useState('loading')
  const [error, setError] = useState(null)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!token) {
      setError('Missing invitation token.')
      setPhase('error')
      return
    }

    apiFetch(`/doctor/invitations/${token}`)
      .then((res) => {
        if (!res.ok) throw new Error('Invalid or expired invitation.')
        return res.json()
      })
      .then((data) => {
        setPreview(data)
        setFullName(data.full_name || '')
        setPhase(data.account_exists ? 'login-required' : 'signup')
      })
      .catch((err) => {
        setError(err.message)
        setPhase('error')
      })
  }, [token])

  async function handleSignup(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const res = await apiFetch('/doctor/signup', {
        method: 'POST',
        json: {
          token,
          username,
          password,
          full_name: fullName.trim() || null,
        },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Signup failed.')
        return
      }

      setCsrfToken(data.csrf_token)
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
        <h1>Doctor Sign Up</h1>

        {phase === 'loading' && <p className="loading">Verifying invitation…</p>}
        {phase === 'error' && <p className="error">{error}</p>}

        {phase === 'login-required' && preview && (
          <div className="setup-card">
            <div className="setup-card__header">
              <h2>Account already exists</h2>
              <p>
                An account exists for <strong>{preview.email}</strong>. Log in to join{' '}
                <strong>{preview.protocol_code}</strong>.
              </p>
            </div>
            <Link
              to={`/doctor/login?token=${encodeURIComponent(token)}`}
              className="btn-primary"
              style={{ textDecoration: 'none', display: 'inline-block' }}
            >
              Go to Login
            </Link>
          </div>
        )}

        {phase === 'signup' && preview && (
          <div className="setup-card">
            <div className="setup-card__header">
              <span className="setup-badge">Study Invitation</span>
              <h2>Join {preview.protocol_code}</h2>
              <p>{preview.study_title}</p>
              <p style={{ marginTop: '8px', fontSize: '13px', color: '#666' }}>
                Signing up as <strong>{preview.email}</strong>
              </p>
            </div>

            <form className="setup-form" onSubmit={handleSignup} noValidate>
              <div className="field">
                <label htmlFor="doctor-username">Username *</label>
                <input
                  id="doctor-username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              <div className="field">
                <label htmlFor="doctor-full-name">Full name</label>
                <input
                  id="doctor-full-name"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="doctor-password">Password *</label>
                <PasswordInput
                  id="doctor-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 12 characters"
                  required
                  autoComplete="new-password"
                />
              </div>
              {error && <p className="error">{error}</p>}
              <button type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? 'Creating account…' : 'Create Account & Join Study'}
              </button>
            </form>
          </div>
        )}
      </main>
    </>
  )
}

export default DoctorSignup
