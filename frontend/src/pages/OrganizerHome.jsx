import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { API_URL } from '../config'
import Header from '../components/Header'

function OrganizerHome() {
  const navigate = useNavigate()
  const location = useLocation()
  const [organizer, setOrganizer] = useState(null)
  const [studies, setStudies] = useState([])
  const [loggingOut, setLoggingOut] = useState(false)
  const successMsg = location.state?.successMsg || null

  function loadStudies() {
    fetch(`${API_URL}/organizer/studies/`, { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : []))
      .then(setStudies)
      .catch(() => {})
  }

  // Verify session on mount and load studies
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
        if (data) {
          setOrganizer(data)
          loadStudies()
        }
      })
      .catch(() => navigate('/organizer/login', { replace: true }))
  }, [navigate])

  async function handleLogout() {

    setLoggingOut(true)
    try {
      await fetch(`${API_URL}/organizer/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Ignore network errors on logout
    }
    navigate('/organizer/login', { replace: true })
  }

  return (
    <>
      <Header>
        {organizer && (
          <button
            id="btn-org-logout"
            className="btn-secondary"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        )}
      </Header>

      <main className="app">
        <h1>Organizer Dashboard</h1>

        {!organizer ? (
          <p className="loading">Verifying session…</p>
        ) : (
          <>
            {/* Welcome card */}
            <div className="status-card" style={{ marginBottom: '28px' }}>
              <div className="label">Session Status</div>
              <p className="message">
                Logged in as <strong>{organizer.username}</strong>
              </p>
            </div>

            {/* Success message banner */}
            {successMsg && <p className="success-msg">{successMsg}</p>}

            {/* Studies Section Header */}
            <div className="section-header">
              <h2 className="section-title">Managed Studies</h2>
              <Link
                id="btn-create-study"
                to="/organizer/studies/new"
                className="btn-primary"
                style={{ textDecoration: 'none' }}
              >
                + Create New Study
              </Link>
            </div>

            {/* Studies Table / Empty State */}
            {studies.length === 0 ? (
              <div className="empty-state">
                <p>No studies created yet.</p>
                <p style={{ marginTop: '8px', color: '#666', fontSize: '13px' }}>
                  Click <strong>+ Create New Study</strong> above to configure your first clinical study.
                </p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Protocol Code</th>
                    <th>Title</th>
                    <th>Blinding</th>
                    <th>Method</th>
                    <th>Sample Size</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {studies.map((study) => (
                    <tr key={study.id}>
                      <td>{study.id}</td>
                      <td>
                        <strong>{study.protocol_code}</strong>
                      </td>
                      <td>{study.title}</td>
                      <td>{study.blinding_type}</td>
                      <td>{study.randomization_method}</td>
                      <td>{study.target_sample_size ?? 'N/A'}</td>
                      <td>
                        <span
                          className={`badge badge--${
                            study.status === 'Active'
                              ? 'active'
                              : 'inactive'
                          }`}
                        >
                          {study.status}
                        </span>
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

export default OrganizerHome
