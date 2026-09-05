import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function InvestigatorChangePassword() {
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Verify session on mount
  useEffect(() => {
    apiFetch('/investigator/me').then(async (res) => {
      if (!res.ok) {
        navigate('/investigator/login', { replace: true })
        return
      }
      const data = await res.json()
      storeCsrfFromResponse(data)
    })
  }, [navigate])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setSubmitting(true)

    try {
      const res = await apiFetch('/investigator/change-password', {
        method: 'POST',
        json: { current_password: currentPassword, new_password: newPassword },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Password change failed.')
        return
      }

      setSuccessMsg('Password changed successfully.')
      setCurrentPassword('')
      setNewPassword('')
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
        <h1>Change Password</h1>

        <div className="setup-card">
          <div className="setup-card__header">
            <span className="setup-badge">Security</span>
            <h2>Set a New Password</h2>
            <p>Enter your current (system-generated) password and choose a new one.</p>
          </div>

          <form className="setup-form" onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="cp-current">Current Password</label>
              <PasswordInput
                id="cp-current"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div className="field">
              <label htmlFor="cp-new">New Password</label>
              <PasswordInput
                id="cp-new"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min. 12 characters"
                required
                autoComplete="new-password"
              />
            </div>
            {error && <p className="error">{error}</p>}
            {successMsg && <p className="success-msg">{successMsg}</p>}
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        </div>
      </main>
    </>
  )
}

export default InvestigatorChangePassword
