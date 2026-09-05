import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'
import Header from '../components/Header'

function parseApiError(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item).join(', ')
  }
  return null
}

function CreateStudy() {
  const navigate = useNavigate()
  const [organizer, setOrganizer] = useState(null)

  // Form state
  const [title, setTitle] = useState('')
  const [protocolCode, setProtocolCode] = useState('')
  const [description, setDescription] = useState('')
  const [blindingType, setBlindingType] = useState('Double-Blind')
  const [emergencyUnblinding, setEmergencyUnblinding] = useState(true)

  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Verify session on mount
  useEffect(() => {
    apiFetch('/organizer/me')
      .then((res) => {
        if (!res.ok) {
          navigate('/organizer/login', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) {
          storeCsrfFromResponse(data)
          setOrganizer(data)
        }
      })
      .catch(() => navigate('/organizer/login', { replace: true }))
  }, [navigate])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    const payload = {
      title: title.trim(),
      protocol_code: protocolCode.trim(),
      description: description.trim() || null,
      blinding_type: blindingType,
      emergency_unblinding_allowed: emergencyUnblinding,
    }

    try {
      const res = await apiFetch('/organizer/studies/', {
        method: 'POST',
        json: payload,
      })
      const data = await res.json()

      if (!res.ok) {
        const message =
          parseApiError(data.detail) ||
          (res.status === 409
            ? `A study with protocol code "${protocolCode.trim()}" already exists. Please use a different protocol code.`
            : 'Failed to create study.')

        if (res.status === 409) {
          document.getElementById('protocol-code')?.focus()
        }

        setError(message)
        return
      }

      // Navigate to the new study's home page
      navigate(`/organizer/studies/${data.id}/home`, {
        state: { successMsg: `Study "${data.title}" created successfully.` },
      })
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
          <h1>Create New Study</h1>
        </div>

        {!organizer ? (
          <p className="loading">Verifying session…</p>
        ) : (
          <div className="study-form-card">
            <div className="setup-card__header">
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span className="setup-badge">Study Configuration</span>
                <span className="badge badge--inactive">Status: Draft</span>
              </div>
              <h2 style={{ marginTop: '8px' }}>Trial Metadata &amp; Protocol Settings</h2>
              <p>Configure basic trial information. You can add treatment arms and randomization settings after creation.</p>
            </div>

            <form className="setup-form" onSubmit={handleSubmit} noValidate>
              {error && <p className="error">{error}</p>}

              <div className="form-grid">
                {/* Title */}
                <div className="field field-full">
                  <label htmlFor="study-title">Title / Full Name *</label>
                  <input
                    id="study-title"
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. A Multi-Center Double-Blind Trial of Drug X"
                    required
                    autoFocus
                  />
                </div>

                {/* Protocol Code */}
                <div className="field">
                  <label htmlFor="protocol-code">Protocol Code *</label>
                  <input
                    id="protocol-code"
                    type="text"
                    value={protocolCode}
                    onChange={(e) => setProtocolCode(e.target.value)}
                    placeholder="e.g. CT-2026-004"
                    required
                  />
                </div>

                {/* Blinding Type */}
                <div className="field">
                  <label htmlFor="blinding-type">Blinding Type</label>
                  <select
                    id="blinding-type"
                    className="select-input"
                    value={blindingType}
                    onChange={(e) => setBlindingType(e.target.value)}
                  >
                    <option value="Double-Blind">Double-Blind</option>
                    <option value="Single-Blind">Single-Blind</option>
                    <option value="Open-Label">Open-Label</option>
                  </select>
                </div>

                {/* Description */}
                <div className="field field-full">
                  <label htmlFor="study-description">Description / Summary</label>
                  <textarea
                    id="study-description"
                    className="textarea-input"
                    rows={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief overview of the trial's objective and methodology..."
                  />
                </div>

                {/* Emergency Unblinding Allowed */}
                <div className="field field-full field-checkbox">
                  <label htmlFor="unblinding-allowed" className="checkbox-label">
                    <input
                      id="unblinding-allowed"
                      type="checkbox"
                      checked={emergencyUnblinding}
                      onChange={(e) => setEmergencyUnblinding(e.target.checked)}
                    />
                    <span>Emergency Unblinding Allowed</span>
                  </label>
                  <span className="field-hint">
                    Permits investigators to perform code-breaks in emergency situations.
                  </span>
                </div>
              </div>

              <div className="form-actions" style={{ marginTop: '24px' }}>
                <button
                  id="btn-create-study-submit"
                  type="submit"
                  className="btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Creating Study…' : 'Create Study'}
                </button>
                <Link
                  to="/organizer/home"
                  className="btn-secondary"
                  style={{ textDecoration: 'none' }}
                >
                  Cancel
                </Link>
              </div>
            </form>
          </div>
        )}
      </main>
    </>
  )
}

export default CreateStudy
