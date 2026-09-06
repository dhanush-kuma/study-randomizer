import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch } from '../api'
import Header from '../components/Header'

function StudyRandomization() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)

  const [targetSampleSize, setTargetSampleSize] = useState('')
  const [randomizationMethod, setRandomizationMethod] = useState('Permuted Block')
  const [blockSizeMin, setBlockSizeMin] = useState('')
  const [blockSizeMax, setBlockSizeMax] = useState('')

  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    apiFetch(`/organizer/studies/${studyId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setStudy(data)
          setTargetSampleSize(data.target_sample_size ?? '')
          setRandomizationMethod(data.randomization_method ?? 'Permuted Block')
          setBlockSizeMin(data.block_size_min ?? '')
          setBlockSizeMax(data.block_size_max ?? '')
        }
      })
      .catch(() => navigate('/organizer/home', { replace: true }))
  }, [studyId, navigate])

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    const min = blockSizeMin !== '' ? parseInt(blockSizeMin, 10) : null
    const max = blockSizeMax !== '' ? parseInt(blockSizeMax, 10) : null

    if (min !== null && min < 1) {
      setError('Block size min must be at least 1.')
      return
    }
    if (max !== null && max < 1) {
      setError('Block size max must be at least 1.')
      return
    }
    if (min !== null && max !== null && max <= min) {
      setError('Block size max must be greater than min.')
      return
    }

    setSubmitting(true)

    const payload = {
      target_sample_size: targetSampleSize !== '' ? parseInt(targetSampleSize, 10) : null,
      randomization_method: randomizationMethod,
      block_size_min: min,
      block_size_max: max,
    }

    try {
      const res = await apiFetch(`/organizer/studies/${studyId}`, {
        method: 'PATCH',
        json: payload,
      })

      if (!res.ok) {
        const data = await res.json()
        setError(data.detail || 'Failed to save randomization settings.')
        return
      }

      navigate(`/organizer/studies/${studyId}/home`, {
        state: { successMsg: 'Randomization settings saved.' },
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
          <Link to={`/organizer/studies/${studyId}/home`} className="back-link">
            ← Back to Study
          </Link>
          <h1>{study ? study.title : 'Loading…'} — Randomization</h1>
        </div>

        {!study ? (
          <p className="loading">Loading study…</p>
        ) : (
          <div className="study-form-card">
            <div className="setup-card__header">
              <span className="setup-badge">Randomization</span>
              <h2 style={{ marginTop: '8px' }}>Randomization Settings</h2>
              <p>Configure the method, block sizing, and target sample size for this trial.</p>
            </div>

            {study.status === 'Active' && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '12px 16px', margin: '16px 24px 0', color: '#991b1b', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>🔒</span>
                <span><strong>Study is Active and locked.</strong> Randomization settings cannot be modified.</span>
              </div>
            )}

            <form className="setup-form" onSubmit={handleSubmit} noValidate>
              {error && <p className="error">{error}</p>}

              <div className="form-grid">
                {/* Randomization Method */}
                <div className="field">
                  <label htmlFor="randomization-method">Randomization Method</label>
                  <select
                    id="randomization-method"
                    className="select-input"
                    value={randomizationMethod}
                    disabled={study.status === 'Active'}
                    onChange={(e) => setRandomizationMethod(e.target.value)}
                  >
                    <option value="Permuted Block">Permuted Block</option>
                    <option value="Simple Random">Simple Random</option>
                    <option value="Minimization">Minimization</option>
                  </select>
                </div>

                {/* Target Sample Size */}
                <div className="field">
                  <label htmlFor="sample-size">Target Sample Size</label>
                  <input
                    id="sample-size"
                    type="number"
                    min="1"
                    value={targetSampleSize}
                    disabled={study.status === 'Active'}
                    onChange={(e) => setTargetSampleSize(e.target.value)}
                    placeholder="e.g. 500"
                  />
                </div>

                {/* Block Size Min */}
                <div className="field">
                  <label htmlFor="block-size-min">Block Size (Min)</label>
                  <input
                    id="block-size-min"
                    type="number"
                    min="1"
                    value={blockSizeMin}
                    disabled={study.status === 'Active'}
                    onChange={(e) => setBlockSizeMin(e.target.value)}
                    placeholder="e.g. 4"
                  />
                  <span className="field-hint">
                    Fixed block size, or minimum if using variable blocks.
                  </span>
                </div>

                {/* Block Size Max */}
                <div className="field">
                  <label htmlFor="block-size-max">Block Size (Max)</label>
                  <input
                    id="block-size-max"
                    type="number"
                    min="1"
                    value={blockSizeMax}
                    disabled={study.status === 'Active'}
                    onChange={(e) => setBlockSizeMax(e.target.value)}
                    placeholder="e.g. 6"
                  />
                  <span className="field-hint">
                    Leave blank to use a fixed block size equal to Min.
                  </span>
                </div>
              </div>

              <div className="form-actions" style={{ marginTop: '24px' }}>
                {study.status !== 'Active' && (
                  <button
                    id="btn-save-randomization"
                    type="submit"
                    className="btn-primary"
                    disabled={submitting}
                  >
                    {submitting ? 'Saving…' : 'Save Randomization Settings'}
                  </button>
                )}
                <Link
                  to={`/organizer/studies/${studyId}/home`}
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

export default StudyRandomization
