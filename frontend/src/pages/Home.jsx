import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function Home() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState('loading')
  const [statusMsg, setStatusMsg] = useState('')
  const [error, setError] = useState(null)

  const [setupToken, setSetupToken] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [showSetup, setShowSetup] = useState(false)

  useEffect(() => {
    apiFetch('/setup/status')
      .then((res) => {
        if (!res.ok) throw new Error('Could not reach backend.')
        return res.json()
      })
      .then((data) => {
        if (data.initialized) {
          navigate('/doctor/login', { replace: true })
        } else {
          setStatusMsg(data.message)
          setPhase('ready')
        }
      })
      .catch((err) => {
        setError(err.message)
        setPhase('error')
      })
  }, [navigate])

  async function handleSetup(e) {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const res = await apiFetch('/setup', {
        method: 'POST',
        json: { setup_token: setupToken, username, password },
      })
      const data = await res.json()
      if (!res.ok) {
        setFormError(data.detail || 'Setup failed.')
        return
      }
      // Setup complete — send the user to the doctor login page
      navigate('/doctor/login', { replace: true })
    } catch {
      setFormError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Header />

      <main className="app">
        <h1>Open Source Study Randomizer</h1>

        {phase === 'loading' && <p className="loading">Checking system status…</p>}
        {phase === 'error' && <p className="error">{error}</p>}

        {phase === 'ready' && (
          <>
            <div className="status-card">
              <div className="label">System Status</div>
              <p className="message">{statusMsg}</p>
            </div>

            <div className="setup-card" style={{ marginTop: '24px' }}>
              <div className="setup-card__header">
                <span className="setup-badge">First-Run Setup</span>
                <h2>Create Admin Account</h2>
                <p>
                  Requires the setup token configured on the server. Only works before
                  an admin account exists.
                </p>
              </div>

              {!showSetup ? (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowSetup(true)}
                >
                  Open setup form
                </button>
              ) : (
                <form className="setup-form" onSubmit={handleSetup} noValidate>
                  <div className="field">
                    <label htmlFor="setup-token">Setup Token</label>
                    <input
                      id="setup-token"
                      type="password"
                      value={setupToken}
                      onChange={(e) => setSetupToken(e.target.value)}
                      placeholder="Server SETUP_TOKEN"
                      autoComplete="off"
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="username">Username</label>
                    <input
                      id="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="admin"
                      required
                      autoComplete="username"
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="password">Password</label>
                    <PasswordInput
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min. 12 characters"
                      required
                      autoComplete="new-password"
                    />
                  </div>
                  {formError && <p className="error">{formError}</p>}
                  <button
                    id="btn-setup-submit"
                    type="submit"
                    className="btn-primary"
                    disabled={submitting}
                  >
                    {submitting ? 'Saving…' : 'Create Account'}
                  </button>
                </form>
              )}
            </div>
          </>
        )}
      </main>
    </>
  )
}

export default Home
