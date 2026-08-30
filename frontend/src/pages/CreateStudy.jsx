import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { API_URL } from '../config'
import Header from '../components/Header'

function CreateStudy() {
  const navigate = useNavigate()
  const [organizer, setOrganizer] = useState(null)

  // Form state
  const [title, setTitle] = useState('')
  const [protocolCode, setProtocolCode] = useState('')
  const [description, setDescription] = useState('')
  const [blindingType, setBlindingType] = useState('Double-Blind')
  const [targetSampleSize, setTargetSampleSize] = useState('')
  const [randomizationMethod, setRandomizationMethod] = useState('Permuted Block')
  const [randomSeed, setRandomSeed] = useState('')
  const [blockSizeRules, setBlockSizeRules] = useState('')
  const [emergencyUnblinding, setEmergencyUnblinding] = useState(true)

  // Treatment Arms state — default to 2 arms with 1:1 allocation ratio
  const [treatmentArms, setTreatmentArms] = useState([
    { name: 'Arm A', short_code: 'ARM_A', allocation_ratio: 1, description: '' },
    { name: 'Arm B', short_code: 'ARM_B', allocation_ratio: 1, description: '' },
  ])

  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Verify session on mount
  useEffect(() => {
    fetch(`${API_URL}/organizer/me`, { credentials: 'include' })
      .then((res) => {
        if (!res.ok) {
          navigate('/organizer/login', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) setOrganizer(data)
      })
      .catch(() => navigate('/organizer/login', { replace: true }))
  }, [navigate])

  function handleArmChange(index, field, value) {
    setTreatmentArms((prev) =>
      prev.map((arm, i) => (i === index ? { ...arm, [field]: value } : arm))
    )
  }

  function handleAddArm() {
    const nextChar = String.fromCharCode(65 + treatmentArms.length)
    setTreatmentArms((prev) => [
      ...prev,
      {
        name: `Arm ${nextChar}`,
        short_code: `ARM_${nextChar}`,
        allocation_ratio: 1,
        description: '',
      },
    ])
  }

  function handleRemoveArm(index) {
    if (treatmentArms.length <= 1) return
    setTreatmentArms((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    // Validate treatment arms
    for (let i = 0; i < treatmentArms.length; i++) {
      const arm = treatmentArms[i]
      if (!arm.name.trim() || !arm.short_code.trim()) {
        setError(`Treatment Arm #${i + 1} requires a valid Name and Short Code.`)
        return
      }
      if (parseInt(arm.allocation_ratio, 10) < 1) {
        setError(`Treatment Arm #${i + 1} allocation ratio must be at least 1.`)
        return
      }
    }

    setSubmitting(true)

    const payload = {
      title: title.trim(),
      protocol_code: protocolCode.trim(),
      description: description.trim() || null,
      blinding_type: blindingType,
      target_sample_size: targetSampleSize ? parseInt(targetSampleSize, 10) : null,
      randomization_method: randomizationMethod,
      random_seed: randomSeed.trim() || null,
      block_size_rules: blockSizeRules.trim() || null,
      emergency_unblinding_allowed: emergencyUnblinding,
      treatment_arms: treatmentArms.map((arm) => ({
        name: arm.name.trim(),
        short_code: arm.short_code.trim(),
        allocation_ratio: parseInt(arm.allocation_ratio, 10) || 1,
        description: arm.description.trim() || null,
      })),
    }

    try {
      const res = await fetch(`${API_URL}/organizer/studies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Failed to create study.')
        return
      }

      // Navigate back to organizer home with created state
      navigate('/organizer/home', {
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
              <h2 style={{ marginTop: '8px' }}>Trial Metadata & Protocol Settings</h2>
              <p>Configure trial parameters and treatment arms for randomization.</p>
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

                {/* Target Sample Size */}
                <div className="field">
                  <label htmlFor="sample-size">Target Sample Size</label>
                  <input
                    id="sample-size"
                    type="number"
                    min="1"
                    value={targetSampleSize}
                    onChange={(e) => setTargetSampleSize(e.target.value)}
                    placeholder="e.g. 500"
                  />
                </div>

                {/* Randomization Method */}
                <div className="field">
                  <label htmlFor="randomization-method">Randomization Method</label>
                  <select
                    id="randomization-method"
                    className="select-input"
                    value={randomizationMethod}
                    onChange={(e) => setRandomizationMethod(e.target.value)}
                  >
                    <option value="Permuted Block">Permuted Block</option>
                    <option value="Simple Random">Simple Random</option>
                    <option value="Minimization">Minimization</option>
                  </select>
                </div>

                {/* Random Seed */}
                <div className="field">
                  <label htmlFor="random-seed">Random Seed</label>
                  <input
                    id="random-seed"
                    type="text"
                    value={randomSeed}
                    onChange={(e) => setRandomSeed(e.target.value)}
                    placeholder="e.g. 4829103 or seed string"
                  />
                </div>

                {/* Block Size Rules */}
                <div className="field">
                  <label htmlFor="block-rules">Block Size Rules</label>
                  <input
                    id="block-rules"
                    type="text"
                    value={blockSizeRules}
                    onChange={(e) => setBlockSizeRules(e.target.value)}
                    placeholder="e.g. Fixed size 4 or Variable 4, 6"
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

              {/* ── Treatment Arms Section ── */}
              <div className="arms-section" style={{ marginTop: '24px' }}>
                <div className="section-header" style={{ marginBottom: '12px' }}>
                  <h3 className="section-title" style={{ fontSize: '15px' }}>
                    Treatment Arms
                  </h3>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleAddArm}
                    style={{ fontSize: '12px', padding: '4px 10px' }}
                  >
                    + Add Treatment Arm
                  </button>
                </div>

                <div className="arms-list">
                  {treatmentArms.map((arm, index) => (
                    <div key={index} className="arm-card">
                      <div className="arm-card__header">
                        <span className="arm-number">Arm #{index + 1}</span>
                        {treatmentArms.length > 1 && (
                          <button
                            type="button"
                            className="btn-danger"
                            onClick={() => handleRemoveArm(index)}
                            title="Remove this treatment arm"
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      <div className="arm-grid">
                        <div className="field">
                          <label htmlFor={`arm-name-${index}`}>Name / Label *</label>
                          <input
                            id={`arm-name-${index}`}
                            type="text"
                            value={arm.name}
                            onChange={(e) =>
                              handleArmChange(index, 'name', e.target.value)
                            }
                            placeholder="e.g. Drug A (100mg Capsule)"
                            required
                          />
                        </div>

                        <div className="field">
                          <label htmlFor={`arm-code-${index}`}>Short Code *</label>
                          <input
                            id={`arm-code-${index}`}
                            type="text"
                            value={arm.short_code}
                            onChange={(e) =>
                              handleArmChange(index, 'short_code', e.target.value)
                            }
                            placeholder="e.g. ARM_A"
                            required
                          />
                        </div>

                        <div className="field">
                          <label htmlFor={`arm-ratio-${index}`}>
                            Allocation Ratio *
                          </label>
                          <input
                            id={`arm-ratio-${index}`}
                            type="number"
                            min="1"
                            value={arm.allocation_ratio}
                            onChange={(e) =>
                              handleArmChange(
                                index,
                                'allocation_ratio',
                                e.target.value
                              )
                            }
                            placeholder="1"
                            required
                          />
                        </div>

                        <div className="field">
                          <label htmlFor={`arm-desc-${index}`}>
                            Description / Notes
                          </label>
                          <input
                            id={`arm-desc-${index}`}
                            type="text"
                            value={arm.description}
                            onChange={(e) =>
                              handleArmChange(index, 'description', e.target.value)
                            }
                            placeholder="Optional dosing instructions or notes"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
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
