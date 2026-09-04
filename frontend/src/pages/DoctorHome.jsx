import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, clearCsrfToken } from '../api'
import Header from '../components/Header'

function DoctorHome() {
  const navigate = useNavigate()
  const [doctor, setDoctor] = useState(null)
  const [studies, setStudies] = useState([])
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    apiFetch('/doctor/me')
      .then((res) => {
        if (!res.ok) {
          navigate('/doctor/login', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (!data) return
        setDoctor(data)
        return apiFetch('/doctor/studies/')
      })
      .then((res) => {
        if (res && res.ok) return res.json()
        return []
      })
      .then((data) => {
        if (Array.isArray(data)) setStudies(data)
      })
      .catch(() => navigate('/doctor/login', { replace: true }))
  }, [navigate])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await apiFetch('/doctor/logout', { method: 'POST' })
      clearCsrfToken()
    } catch {
      // Ignore network errors on logout
    }
    navigate('/doctor/login', { replace: true })
  }

  return (
    <>
      <Header>
        {doctor && (
          <button
            className="btn-secondary"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        )}
      </Header>

      <main className="app">
        <h1>Doctor Dashboard</h1>

        {!doctor ? (
          <p className="loading">Verifying session…</p>
        ) : (
          <>
            <div className="status-card" style={{ marginBottom: '28px' }}>
              <div className="label">Session Status</div>
              <p className="message">
                Logged in as <strong>{doctor.full_name || doctor.username}</strong>{' '}
                ({doctor.email})
              </p>
            </div>

            <div className="section-header">
              <h2 className="section-title">My Studies</h2>
            </div>

            {studies.length === 0 ? (
              <div className="empty-state">
                <p>You are not assigned to any studies yet.</p>
                <p style={{ marginTop: '8px', color: '#666', fontSize: '13px' }}>
                  Ask your study organizer to send you an email invitation.
                </p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Protocol Code</th>
                    <th>Title</th>
                    <th>Blinding</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {studies.map((study) => (
                    <tr key={study.id}>
                      <td>
                        <strong>{study.protocol_code}</strong>
                      </td>
                      <td>{study.title}</td>
                      <td>{study.blinding_type}</td>
                      <td>
                        <span
                          className={`badge badge--${
                            study.status === 'Active' ? 'active' : 'inactive'
                          }`}
                        >
                          {study.status}
                        </span>
                      </td>
                      <td>{new Date(study.joined_at).toLocaleDateString()}</td>
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

export default DoctorHome
