import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiFetch, clearCsrfToken, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

function InvestigatorHome() {
  const navigate = useNavigate()
  const [investigator, setInvestigator] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)

  // Patient randomization form state
  const [patientId, setPatientId] = useState('')
  const [assignedRecord, setAssignedRecord] = useState(null)
  const [assignedList, setAssignedList] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  // Emergency unblinding state
  const [unblindedRecords, setUnblindedRecords] = useState({})
  const [unblindModalRecord, setUnblindModalRecord] = useState(null)
  const [unblindError, setUnblindError] = useState(null)
  const [unblindingSubmitting, setUnblindingSubmitting] = useState(false)

  function loadAssignments() {
    apiFetch('/investigator/assignments')
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (Array.isArray(data)) {
          setAssignedList(data)
        }
      })
      .catch(() => {})
  }

  useEffect(() => {
    apiFetch('/investigator/me')
      .then((res) => {
        if (!res.ok) {
          navigate('/investigator/login', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) {
          storeCsrfFromResponse(data)
          setInvestigator(data)
          loadAssignments()
        }
      })
      .catch(() => navigate('/investigator/login', { replace: true }))
  }, [navigate])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await apiFetch('/investigator/logout', { method: 'POST' })
      clearCsrfToken()
    } catch {
      // Ignore network errors on logout
    }
    navigate('/investigator/login', { replace: true })
  }

  async function handleAssignKit(e) {
    e.preventDefault()
    setError(null)
    setAssignedRecord(null)

    const trimmed = patientId.trim()
    if (!trimmed) {
      setError('Please enter a valid Patient ID.')
      return
    }

    setSubmitting(true)

    try {
      const res = await apiFetch('/investigator/assign-kit', {
        method: 'POST',
        json: { patient_id: trimmed },
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to assign kit code.')
        return
      }

      setAssignedRecord(data)
      setPatientId('')
      loadAssignments()
    } catch {
      setError('Could not connect to backend.')
    } finally {
      setSubmitting(false)
    }
  }

  function handleOpenUnblindModal(rec) {
    setUnblindError(null)
    setUnblindModalRecord(rec)
  }

  function handleCloseUnblindModal() {
    if (unblindingSubmitting) return
    setUnblindModalRecord(null)
    setUnblindError(null)
  }

  async function handleConfirmUnblind() {
    if (!unblindModalRecord) return
    setUnblindError(null)
    setUnblindingSubmitting(true)

    try {
      const res = await apiFetch(`/investigator/records/${unblindModalRecord.id}/unblind`, {
        method: 'POST',
      })
      const data = await res.json()

      if (!res.ok) {
        const msg = data.detail || 'Emergency unblinding failed.'
        setUnblindError(msg)
        return
      }

      setUnblindedRecords((prev) => ({
        ...prev,
        [unblindModalRecord.id]: data.treatment_name,
      }))
      setUnblindModalRecord(null)
    } catch {
      setUnblindError('Could not connect to backend.')
    } finally {
      setUnblindingSubmitting(false)
    }
  }

  const isDoubleBlind = investigator?.blinding_type === 'Double-Blind'

  return (
    <>
      <Header>
        {investigator && (
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <Link
              to="/investigator/change-password"
              className="btn-primary"
              style={{ textDecoration: 'none', padding: '6px 14px', fontSize: '13px' }}
            >
              Change Password
            </Link>
            <button
              className="btn-secondary"
              onClick={handleLogout}
              disabled={loggingOut}
            >
              {loggingOut ? 'Logging out…' : 'Log out'}
            </button>
          </div>
        )}
      </Header>

      <main className="app">
        {!investigator ? (
          <p className="loading">Verifying session…</p>
        ) : (
          <>
            <h1>{investigator.study_title || 'Investigator Dashboard'}</h1>

            {investigator.study_description && (
              <p style={{ fontSize: '15px', color: '#444', marginTop: '0', marginBottom: '24px', lineHeight: '1.5' }}>
                {investigator.study_description}
              </p>
            )}

            <div className="status-card" style={{ marginBottom: '28px' }}>
              <div className="label">Session Status</div>
              <p className="message">
                Logged in as <strong>{investigator.name || investigator.username}</strong>
                {' '}· Trial ID: <strong>{investigator.trial_id}</strong>
                {' '}· Username: <code>{investigator.username}</code>
              </p>
            </div>

            {/* Randomization & Kit Assignment Form */}
            <div className="study-form-card" style={{ marginTop: '24px' }}>
              <div className="setup-card__header">
                <span className="setup-badge">Randomization & Kit Assignment</span>
                <h2 style={{ marginTop: '8px' }}>Assign Kit Code for Patient</h2>
                <p>Enter the Patient ID to randomize subject and assign the next sequence kit code.</p>
              </div>

              <form className="setup-form" onSubmit={handleAssignKit} noValidate>
                {error && <p className="error">{error}</p>}

                {assignedRecord && (
                  <div className="success-msg">Kit code assigned.</div>
                )}

                <div className="form-grid">
                  <div className="field field-full">
                    <label htmlFor="patient-id">Patient ID / Subject ID *</label>
                    <input
                      id="patient-id"
                      type="text"
                      value={patientId}
                      onChange={(e) => setPatientId(e.target.value)}
                      placeholder="e.g. PAT-1001"
                      required
                    />
                    <span className="field-hint">
                      Note: Patient ID must be unique within the study to maintain auditability and support emergency unblinding if required.
                    </span>
                  </div>
                </div>

                <div className="form-actions" style={{ marginTop: '20px' }}>
                  <button
                    id="btn-assign-kit"
                    type="submit"
                    className="btn-primary"
                    disabled={submitting || !patientId.trim()}
                  >
                    {submitting ? 'Assigning Kit Code…' : 'Assign Kit Code'}
                  </button>
                </div>
              </form>
            </div>

            {/* Recent Kit Assignments */}
            {assignedList.length > 0 && (
              <div style={{ marginTop: '36px' }}>
                <div className="section-header">
                  <h2 className="section-title">Assigned Patient Records ({assignedList.length})</h2>
                </div>

                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Patient ID</th>
                      <th>Kit Code</th>
                      <th>Treatment Arm</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignedList.map((rec, index) => (
                      <tr key={rec.id}>
                        <td>{index + 1}</td>
                        <td><strong>{rec.assigned_patient_id}</strong></td>
                        <td><code>{rec.kit_code}</code></td>
                        <td>
                          {!isDoubleBlind ? (
                            <span>{rec.treatment_name}</span>
                          ) : !rec.blind || unblindedRecords[rec.id] ? (
                            <span
                              style={{
                                color: '#b91c1c',
                                fontWeight: '600',
                                background: '#fef2f2',
                                padding: '2px 8px',
                                borderRadius: '3px',
                                border: '1px solid #fecaca',
                                fontSize: '13px',
                              }}
                            >
                              Unblinded: {unblindedRecords[rec.id] || rec.treatment_name}
                            </span>
                          ) : (
                            <button
                              className="btn-secondary"
                              style={{ padding: '3px 10px', fontSize: '12px' }}
                              onClick={() => handleOpenUnblindModal(rec)}
                            >
                              Unblind
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>

      {/* Emergency Unblinding Modal */}
      {unblindModalRecord && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="setup-card"
            style={{
              maxWidth: '440px',
              width: '90%',
              background: '#ffffff',
              padding: '24px',
              borderRadius: '6px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '17px', color: '#1a1a2e' }}>Emergency Unblinding Notice</h3>
            </div>

            <p style={{ fontSize: '14px', color: '#444', lineHeight: '1.5', margin: '0 0 14px' }}>
              You are requesting to unblind the treatment arm for Patient <strong>{unblindModalRecord.assigned_patient_id}</strong> (Kit <code>{unblindModalRecord.kit_code}</code>).
            </p>

            <p
              style={{
                fontSize: '13px',
                color: '#854d0e',
                background: '#fefce8',
                border: '1px solid #fef08a',
                padding: '10px 12px',
                borderRadius: '4px',
                margin: '0 0 16px',
                lineHeight: '1.4',
              }}
            >
              <strong>Notice:</strong> This unblinding event will be permanently recorded in the audit log and made visible to the study organizer.
            </p>

            {unblindError && (
              <p className="error" style={{ marginBottom: '16px' }}>
                {unblindError}
              </p>
            )}

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleCloseUnblindModal}
                disabled={unblindingSubmitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-danger"
                onClick={handleConfirmUnblind}
                disabled={unblindingSubmitting}
              >
                {unblindingSubmitting ? 'Unblinding…' : 'Confirm Unblind'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default InvestigatorHome
