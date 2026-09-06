import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearCsrfToken, storeCsrfFromResponse } from '../api'
import PasswordInput from '../components/PasswordInput'
import Header from '../components/Header'

function AdminHome() {
  const navigate = useNavigate()
  const [admin, setAdmin] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)

  // Organizer list & form state
  const [organizers, setOrganizers] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [orgUsername, setOrgUsername] = useState('')
  const [orgPassword, setOrgPassword] = useState('')
  const [formError, setFormError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [successMsg, setSuccessMsg] = useState(null)
  const [togglingId, setTogglingId] = useState(null)  // id of row being toggled

  // Verify session on mount and load organizers
  useEffect(() => {
    apiFetch('/admin/me')
      .then((res) => {
        if (!res.ok) { navigate('/admin/login', { replace: true }); return null }
        return res.json()
      })
      .then((data) => { if (data) { storeCsrfFromResponse(data); setAdmin(data); loadOrganizers() } })
      .catch(() => navigate('/admin/login', { replace: true }))
  }, [navigate])

  function loadOrganizers() {
    apiFetch('/admin/organizers/')
      .then((res) => res.ok ? res.json() : [])
      .then(setOrganizers)
      .catch(() => {})
  }

  async function handleLogout() {
    setLoggingOut(true)
    await apiFetch('/admin/logout', { method: 'POST' })
    clearCsrfToken()
    navigate('/admin/login', { replace: true })
  }

  async function handleCreateOrganizer(e) {
    e.preventDefault()
    setFormError(null)
    setSuccessMsg(null)
    setSubmitting(true)

    try {
      const res = await apiFetch('/admin/organizers/', {
        method: 'POST',
        json: { username: orgUsername, password: orgPassword },
      })
      const data = await res.json()

      if (!res.ok) {
        setFormError(data.detail || 'Failed to create organizer.')
        return
      }

      setSuccessMsg(`Organizer "${data.username}" created successfully.`)
      setOrgUsername('')
      setOrgPassword('')
      setShowForm(false)
      loadOrganizers()
    } catch {
      setFormError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  function cancelForm() {
    setShowForm(false)
    setFormError(null)
    setOrgUsername('')
    setOrgPassword('')
  }

  return (
    <>
      <Header>
        {admin && (
          <button
            id="btn-logout"
            className="btn-secondary"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        )}
      </Header>


      <main className="app">
        <h1>Admin Dashboard</h1>

        {!admin ? (
          <p className="loading">Loading…</p>
        ) : (
          <>
            {/* ── Welcome card ── */}
            <div className="status-card" style={{ marginBottom: '28px' }}>
              <div className="label">Session</div>
              <p className="message">
                Logged in as <strong>{admin.username}</strong>
              </p>
            </div>

            {/* ── Organizer section ── */}
            <div className="section-header">
              <h2 className="section-title">Organizers</h2>
              {!showForm && (
                <button
                  id="btn-create-organizer"
                  className="btn-primary"
                  onClick={() => { setSuccessMsg(null); setShowForm(true) }}
                >
                  + Create Organizer
                </button>
              )}
            </div>

            {/* Success banner */}
            {successMsg && (
              <p className="success-msg">{successMsg}</p>
            )}

            {/* ── Create organizer form ── */}
            {showForm && (
              <div className="setup-card" style={{ marginBottom: '20px' }}>
                <div className="setup-card__header">
                  <span className="setup-badge">New Organizer</span>
                  <h2>Create Organizer Account</h2>
                  <p>The organizer will be able to manage study sessions.</p>
                </div>
                <form className="setup-form" onSubmit={handleCreateOrganizer} noValidate>
                  <div className="field">
                    <label htmlFor="org-username">Username</label>
                    <input
                      id="org-username"
                      type="text"
                      value={orgUsername}
                      onChange={(e) => setOrgUsername(e.target.value)}
                      placeholder="organizer_name"
                      required
                      autoFocus
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="org-password">Password</label>
                    <PasswordInput
                      id="org-password"
                      value={orgPassword}
                      onChange={(e) => setOrgPassword(e.target.value)}
                      placeholder="Min. 12 characters"
                      required
                    />
                  </div>
                  {formError && <p className="error">{formError}</p>}
                  <div className="form-actions">
                    <button id="btn-org-submit" type="submit" className="btn-primary" disabled={submitting}>
                      {submitting ? 'Creating…' : 'Create Organizer'}
                    </button>
                    <button type="button" className="btn-secondary" onClick={cancelForm}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* ── Organizer table ── */}
            {organizers.length === 0 ? (
              <p className="empty-state">No organizers yet. Create one above.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Username</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {organizers.map((org) => (
                    <tr key={org.id}>
                      <td>{org.id}</td>
                      <td>{org.username}</td>
                      <td>
                        <span className={`badge badge--${org.is_active ? 'active' : 'inactive'}`}>
                          {org.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <button
                          className={org.is_active ? 'btn-danger' : 'btn-restore'}
                          disabled={togglingId === org.id}
                          onClick={async () => {
                            setTogglingId(org.id)
                            try {
                              const res = await apiFetch(
                                `/admin/organizers/${org.id}/status`,
                                { method: 'PATCH' }
                              )
                              if (res.ok) {
                                const updated = await res.json()
                                setOrganizers((prev) =>
                                  prev.map((o) => (o.id === updated.id ? updated : o))
                                )
                              }
                            } finally {
                              setTogglingId(null)
                            }
                          }}
                        >
                          {togglingId === org.id
                            ? '…'
                            : org.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </main>
    </>
  )
}

export default AdminHome
