import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom'
import { apiFetch } from '../api'
import Header from '../components/Header'

function StudyHome() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [study, setStudy] = useState(null)
  const successMsg = location.state?.successMsg || null

  useEffect(() => {
    apiFetch(`/organizer/studies/${studyId}`)
      .then((res) => {
        if (!res.ok) {
          navigate('/organizer/home', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => { if (data) setStudy(data) })
      .catch(() => navigate('/organizer/home', { replace: true }))
  }, [studyId, navigate])

  return (
    <>
      <Header />
      <main className="app">
        <div className="page-header">
          <Link to="/organizer/home" className="back-link">
            ← Back to Studies
          </Link>
          <h1>{study ? study.title : 'Loading…'}</h1>
        </div>

        {successMsg && <p className="success-msg">{successMsg}</p>}

        {study && (
          <>
            {/* Study meta */}
            <div className="status-card" style={{ marginBottom: '32px' }}>
              <div className="label">Protocol</div>
              <p className="message">
                <strong>{study.protocol_code}</strong>
                {' · '}
                <span className={`badge badge--${study.status === 'Active' ? 'active' : 'inactive'}`}>
                  {study.status}
                </span>
                {' · '}
                {study.blinding_type}
              </p>
            </div>

            {/* Action cards */}
            <div className="section-header">
              <h2 className="section-title">Study Setup</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '16px' }}>

              {/* Treatment Arms */}
              <div className="study-form-card" style={{ maxWidth: 'none' }}>
                <div className="setup-card__header">
                  <span className="setup-badge">Arms</span>
                  <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Treatment Arms</h2>
                  <p style={{ marginTop: '4px' }}>
                    Define the treatment arms and allocation ratios for this trial.
                  </p>
                </div>
                <div style={{ padding: '16px 20px' }}>
                  <Link
                    id="btn-study-arms"
                    to={`/organizer/studies/${studyId}/arms`}
                    className="btn-primary"
                    style={{ textDecoration: 'none' }}
                  >
                    Manage Arms →
                  </Link>
                </div>
              </div>

              {/* Randomization */}
              <div className="study-form-card" style={{ maxWidth: 'none' }}>
                <div className="setup-card__header">
                  <span className="setup-badge">Randomization</span>
                  <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Randomization Settings</h2>
                  <p style={{ marginTop: '4px' }}>
                    Configure the randomization method, block sizing, and target sample size.
                  </p>
                </div>
                <div style={{ padding: '16px 20px' }}>
                  <Link
                    id="btn-study-randomization"
                    to={`/organizer/studies/${studyId}/randomization`}
                    className="btn-primary"
                    style={{ textDecoration: 'none' }}
                  >
                    Configure →
                  </Link>
                </div>
              </div>

              {/* Upload CSV */}
              <div className="study-form-card" style={{ maxWidth: 'none' }}>
                <div className="setup-card__header">
                  <span className="setup-badge">Data</span>
                  <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Upload CSV</h2>
                  <p style={{ marginTop: '4px' }}>
                    Import participant data or baseline covariates from a CSV file.
                  </p>
                </div>
                <div style={{ padding: '16px 20px' }}>
                  <Link
                    id="btn-study-upload"
                    to={`/organizer/studies/${studyId}/upload-csv`}
                    className="btn-primary"
                    style={{ textDecoration: 'none' }}
                  >
                    Upload CSV →
                  </Link>
                </div>
              </div>

            </div>
          </>
        )}
      </main>
    </>
  )
}

export default StudyHome
