import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { apiFetch } from '../api'

function DoctorGuard() {
  const [destination, setDestination] = useState(null)

  useEffect(() => {
    apiFetch('/doctor/me')
      .then((res) => {
        setDestination(res.ok ? '/doctor/home' : '/doctor/login')
      })
      .catch(() => setDestination('/doctor/login'))
  }, [])

  if (!destination) return <p className="loading">Checking session…</p>
  return <Navigate to={destination} replace />
}

export default DoctorGuard
