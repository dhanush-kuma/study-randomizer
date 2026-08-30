import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_URL } from '../config'

function AdminHome() {
  const navigate = useNavigate()
  const [admin, setAdmin] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)

  // Verify the session is still valid when this page mounts
  useEffect(() => {
    fetch(`${API_URL}/admin/me`, { credentials: 'include' })
      .then((res) => {
        if (!res.ok) { navigate('/admin/login', { replace: true }); return }
        return res.json()
      })
      .then((data) => data && setAdmin(data))
      .catch(() => navigate('/admin/login', { replace: true }))
  }, [navigate])

  async function handleLogout() {
    setLoggingOut(true)
    await fetch(`${API_URL}/admin/logout`, {
      method: 'POST',
      credentials: 'include',
    })
    navigate('/admin/login', { replace: true })
  }

  return (
    <>
      <header className="app-header">
        <span className="site-name">Study Randomizer</span>
        {admin && (
          <button
            id="btn-logout"
            className="btn-secondary"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
        )}
      </header>

      <main className="app">
        <h1>Admin Dashboard</h1>

        {!admin ? (
          <p className="loading">Loading…</p>
        ) : (
          <div className="status-card">
            <div className="label">Session</div>
            <p className="message">
              ✓ Login successful — welcome, <strong>{admin.username}</strong>.
            </p>
          </div>
        )}
      </main>
    </>
  )
}

export default AdminHome
