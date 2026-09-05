import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch } from '../api'
import Header from '../components/Header'

function UploadCSV() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const [study, setStudy] = useState(null)

  useEffect(() => {
    apiFetch(`/organizer/studies/${studyId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => { if (data) setStudy(data) })
      .catch(() => navigate('/organizer/home', { replace: true }))
  }, [studyId, navigate])

  return (
    <>
      <Header />
      <main className="app">
        <div className="page-header">
          <Link to={`/organizer/studies/${studyId}/home`} className="back-link">
            ← Back to Study
          </Link>
          <h1>{study ? study.title : 'Loading…'} — Upload CSV</h1>
        </div>

        <div className="empty-state">
          <p>CSV upload functionality coming soon.</p>
          <p style={{ marginTop: '8px', color: '#666', fontSize: '13px' }}>
            This page is under construction.
          </p>
        </div>
      </main>
    </>
  )
}

export default UploadCSV
