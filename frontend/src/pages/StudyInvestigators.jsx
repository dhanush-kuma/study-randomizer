import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

const STATUS_LABELS = {
  inactive: { label: 'Inactive', cls: 'badge--inactive' },
  active:   { label: 'Active',   cls: 'badge--active'   },
  revoked:  { label: 'Revoked',  cls: 'badge--inactive' },
}

function StudyInvestigators() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)
  const [investigators, setInvestigators] = useState([])
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [actionLoading, setActionLoading] = useState(null) // id of investigator being updated
  const [pendingAction, setPendingAction] = useState(null) // { type, id, label }

  function loadInvestigators() {
    apiFetch(`/organizer/studies/${studyId}/investigators`)
      .then((res) => (res.ok ? res.json() : []))
      .then(setInvestigators)
      .catch(() => {})
  }

  useEffect(() => {
    apiFetch('/organizer/me')
      .then(async (res) => {
        if (!res.ok) {
          navigate('/organizer/login', { replace: true })
          return null
        }
        const me = await res.json()
        storeCsrfFromResponse(me)
        return Promise.all([
          apiFetch(`/organizer/studies/${studyId}`),
          apiFetch(`/organizer/studies/${studyId}/investigators`),
        ])
      })
      .then((result) => {
        if (!result) return
        const [studyRes, invRes] = result
        if (!studyRes.ok) {
          navigate('/organizer/home', { replace: true })
          return
        }
        return Promise.all([studyRes.json(), invRes.ok ? invRes.json() : []])
      })
      .then((data) => {
        if (!data) return
        setStudy(data[0])
        setInvestigators(data[1])
      })
      .catch(() => navigate('/organizer/login', { replace: true }))
  }, [navigate, studyId])

  async function handleInvite(e) {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setSubmitting(true)

    try {
      const res = await apiFetch(`/organizer/studies/${studyId}/investigators`, {
        method: 'POST',
        json: { email: email.trim(), name: name.trim() || null },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to add investigator.')
        return
      }

      setSuccessMsg(
        `Investigator added (username: ${data.username}). Credentials sent to ${data.email}.`
      )
      setEmail('')
      setName('')
      loadInvestigators()
    } catch {
      setError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRevoke(investigatorId) {
    setActionLoading(investigatorId)
    try {
      const res = await apiFetch(
        `/organizer/studies/${studyId}/investigators/${investigatorId}/revoke`,
        { method: 'PATCH' }
      )
      if (!res.ok) {
        const data = await res.json()
        alert(data.detail || 'Failed to revoke access.')
        return
      }
      setPendingAction(null)
      loadInvestigators()
    } catch {
      alert('Could not connect to backend.')
    } finally {
      setActionLoading(null)
    }
  }

  async function handleRestore(investigatorId) {
    setActionLoading(investigatorId)
    try {
      const res = await apiFetch(
        `/organizer/studies/${studyId}/investigators/${investigatorId}/restore`,
        { method: 'PATCH' }
      )
      if (!res.ok) {
        const data = await res.json()
        alert(data.detail || 'Failed to restore access.')
        return
      }
      setPendingAction(null)
      setSuccessMsg('Investigator access restored. They can log in again with their existing credentials.')
      loadInvestigators()
    } catch {
      alert('Could not connect to backend.')
    } finally {
      setActionLoading(null)
    }
  }

  function investigatorLabel(inv) {
    return inv.name || inv.username
  }

  return (
    <>
      <Header />

      <main className="app">
        <div className="page-header">
          <Link to={`/organizer/studies/${studyId}/home`} className="back-link">
            ← Back to Study
          </Link>
          <h1>Investigators</h1>
        </div>

        {!study ? (
          <p className="loading">Loading study…</p>
        ) : (
          <>
            <div className="status-card" style={{ marginBottom: '24px' }}>
              <div className="label">Study</div>
              <p className="message">
                <strong>{study.protocol_code}</strong> — {study.title}
              </p>
            </div>

            {/* Invite form */}
            <div className="setup-card">
              <div className="setup-card__header">
                <span className="setup-badge">Add Investigator</span>
                <h2>Invite an investigator</h2>
                <p>
                  The system will generate a username and temporary password and send them
                  to the provided email address.
                </p>
              </div>

              <form className="setup-form" onSubmit={handleInvite} noValidate>
                <div className="field">
                  <label htmlFor="inv-email">Email *</label>
                  <input
                    id="inv-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="investigator@hospital.org"
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="inv-name">Full name (optional)</label>
                  <input
                    id="inv-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Dr. Jane Smith"
                  />
                </div>
                {error && <p className="error">{error}</p>}
                {successMsg && <p className="success-msg">{successMsg}</p>}
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? 'Adding…' : 'Add Investigator'}
                </button>
              </form>
            </div>

            {/* Investigators table */}
            <div className="section-header" style={{ marginTop: '32px' }}>
              <h2 className="section-title">Investigators</h2>
            </div>

            {investigators.length === 0 ? (
              <div className="empty-state">
                <p>No investigators added yet.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Added</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {investigators.map((inv) => {
                    const badge = STATUS_LABELS[inv.status] || { label: inv.status, cls: 'badge--inactive' }
                    return (
                      <tr key={inv.id}>
                        <td><code>{inv.username}</code></td>
                        <td>{inv.name || '—'}</td>
                        <td>{inv.email}</td>
                        <td>
                          <span className={`badge ${badge.cls}`}>{badge.label}</span>
                        </td>
                        <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                        <td>
                          {pendingAction?.id === inv.id ? (
                            <div className="action-confirm">
                              <p className="action-confirm__text">
                                {pendingAction.type === 'revoke'
                                  ? `Revoke access for ${pendingAction.label}? They will no longer be able to log in.`
                                  : `Restore access for ${pendingAction.label}? They can log in again with their existing credentials.`}
                              </p>
                              <div className="action-confirm__buttons">
                                <button
                                  type="button"
                                  className={pendingAction.type === 'revoke' ? 'btn-danger' : 'btn-primary'}
                                  style={{ fontSize: '12px', padding: '4px 10px' }}
                                  disabled={actionLoading === inv.id}
                                  onClick={() =>
                                    pendingAction.type === 'revoke'
                                      ? handleRevoke(inv.id)
                                      : handleRestore(inv.id)
                                  }
                                >
                                  {actionLoading === inv.id
                                    ? 'Saving…'
                                    : pendingAction.type === 'revoke'
                                      ? 'Yes, revoke'
                                      : 'Yes, restore'}
                                </button>
                                <button
                                  type="button"
                                  className="btn-secondary"
                                  style={{ fontSize: '12px', padding: '4px 10px' }}
                                  disabled={actionLoading === inv.id}
                                  onClick={() => setPendingAction(null)}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : inv.status === 'revoked' ? (
                            <button
                              className="btn-secondary"
                              style={{ fontSize: '12px', padding: '4px 10px' }}
                              disabled={actionLoading === inv.id}
                              onClick={() =>
                                setPendingAction({
                                  type: 'restore',
                                  id: inv.id,
                                  label: investigatorLabel(inv),
                                })
                              }
                            >
                              Restore access
                            </button>
                          ) : (
                            <button
                              className="btn-secondary"
                              style={{ fontSize: '12px', padding: '4px 10px' }}
                              disabled={actionLoading === inv.id}
                              onClick={() =>
                                setPendingAction({
                                  type: 'revoke',
                                  id: inv.id,
                                  label: investigatorLabel(inv),
                                })
                              }
                            >
                              Revoke
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </>
        )}
      </main>
    </>
  )
}

export default StudyInvestigators
