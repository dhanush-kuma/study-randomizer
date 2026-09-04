import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { apiFetch } from '../api'
import Header from '../components/Header'

function StudyInvites() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)
  const [invitations, setInvitations] = useState([])
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  function loadInvitations() {
    apiFetch(`/organizer/studies/${studyId}/invitations`)
      .then((res) => (res.ok ? res.json() : []))
      .then(setInvitations)
      .catch(() => {})
  }

  useEffect(() => {
    apiFetch('/organizer/me')
      .then((res) => {
        if (!res.ok) {
          navigate('/organizer/login', { replace: true })
          return null
        }
        return Promise.all([
          apiFetch(`/organizer/studies/${studyId}`),
          apiFetch(`/organizer/studies/${studyId}/invitations`),
        ])
      })
      .then((result) => {
        if (!result) return
        const [studyRes, invitesRes] = result
        if (!studyRes.ok) {
          navigate('/organizer/home', { replace: true })
          return
        }
        return Promise.all([studyRes.json(), invitesRes.ok ? invitesRes.json() : []])
      })
      .then((data) => {
        if (!data) return
        setStudy(data[0])
        setInvitations(data[1])
      })
      .catch(() => navigate('/organizer/login', { replace: true }))
  }, [navigate, studyId])

  async function handleInvite(e) {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setSubmitting(true)

    try {
      const res = await apiFetch(`/organizer/studies/${studyId}/invitations`, {
        method: 'POST',
        json: { email: email.trim(), full_name: fullName.trim() || null },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to send invitation.')
        return
      }

      setSuccessMsg(`Invitation sent to ${data.email}.`)
      setEmail('')
      setFullName('')
      loadInvitations()
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
        <div className="page-header">
          <Link to="/organizer/home" className="back-link">
            ← Back to Studies
          </Link>
          <h1>Invite Doctors</h1>
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

            <div className="setup-card">
              <div className="setup-card__header">
                <span className="setup-badge">Email Invitation</span>
                <h2>Invite a doctor</h2>
                <p>
                  Enter the doctor&apos;s email. They will receive a link to create an
                  account and join this study.
                </p>
              </div>

              <form className="setup-form" onSubmit={handleInvite} noValidate>
                <div className="field">
                  <label htmlFor="invite-email">Email *</label>
                  <input
                    id="invite-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="doctor@hospital.org"
                    required
                  />
                </div>
                <div className="field">
                  <label htmlFor="invite-name">Full name (optional)</label>
                  <input
                    id="invite-name"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Jane Smith"
                  />
                </div>
                {error && <p className="error">{error}</p>}
                {successMsg && <p className="success-msg">{successMsg}</p>}
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? 'Sending…' : 'Send Invitation'}
                </button>
              </form>
            </div>

            <div className="section-header" style={{ marginTop: '32px' }}>
              <h2 className="section-title">Sent Invitations</h2>
            </div>

            {invitations.length === 0 ? (
              <div className="empty-state">
                <p>No invitations sent yet.</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Sent</th>
                    <th>Expires</th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.map((inv) => (
                    <tr key={inv.id}>
                      <td>{inv.email}</td>
                      <td>{inv.full_name || '—'}</td>
                      <td>
                        <span className={`badge badge--${inv.status === 'pending' ? 'inactive' : 'active'}`}>
                          {inv.status}
                        </span>
                      </td>
                      <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                      <td>{new Date(inv.expires_at).toLocaleDateString()}</td>
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

export default StudyInvites
