import { useEffect, useState } from 'react'
import { API_URL } from '../config'

function Home() {
  const [phase, setPhase] = useState('loading')
  const [statusMsg, setStatusMsg] = useState('')
  const [error, setError] = useState(null)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => {
        if (!res.ok) throw new Error('Could not reach backend.')
        return res.json()
      })
      .then((data) => {
        if (data.initialized) {
          setStatusMsg(data.message)
          setPhase('ready')
        } else {
          setPhase('setup')
        }
      })
      .catch((err) => {
        setError(err.message)
        setPhase('error')
      })
  }, [])

  async function handleSetup(e) {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json()
      if (!res.ok) { setFormError(data.detail || 'Setup failed.'); return }
      setStatusMsg(data.message)
      setPhase('ready')
    } catch {
      setFormError('Could not connect to backend.')
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
        <h1>Open Source Study Randomizer</h1>

        {phase === 'loading' && <p className="loading">Checking system status…</p>}
        {phase === 'error'   && <p className="error">{error}</p>}

        {phase === 'setup' && (
          <div className="setup-card">
            <div className="setup-card__header">
              <span className="setup-badge">First-Run Setup</span>
              <h2>Create Admin Account</h2>
              <p>No admin account found. Set up your credentials to continue.</p>
            </div>
            <form className="setup-form" onSubmit={handleSetup} noValidate>
              <div className="field">
                <label htmlFor="username">Username</label>
                <input id="username" type="text" value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin" required autoComplete="username" />
              </div>
              <div className="field">
                <label htmlFor="password">Password</label>
                <input id="password" type="password" value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 6 characters" required autoComplete="new-password" />
              </div>
              {formError && <p className="error">{formError}</p>}
              <button id="btn-setup-submit" type="submit" className="btn-primary" disabled={submitting}>
                {submitting ? 'Saving…' : 'Create Account'}
              </button>
            </form>
          </div>
        )}

        {phase === 'ready' && (
          <div className="status-card">
            <div className="label">System Status</div>
            <p className="message">{statusMsg}</p>
          </div>
        )}
      </main>
    </>
  )
}

export default Home
