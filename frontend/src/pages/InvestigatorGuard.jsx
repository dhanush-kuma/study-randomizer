import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../api'

/**
 * Guard for /investigator — redirects to login if no active session,
 * or to /investigator/home if the investigator is already authenticated.
 */
function InvestigatorGuard() {
  const navigate = useNavigate()

  useEffect(() => {
    apiFetch('/investigator/me')
      .then((res) => {
        if (res.ok) {
          navigate('/investigator/home', { replace: true })
        } else {
          navigate('/investigator/login', { replace: true })
        }
      })
      .catch(() => navigate('/investigator/login', { replace: true }))
  }, [navigate])

  return null
}

export default InvestigatorGuard
