import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch, storeCsrfFromResponse } from '../api'

/**
 * Guard for /investigator — redirects to login if no active session,
 * or to /investigator/home if the investigator is already authenticated.
 */
function InvestigatorGuard() {
  const navigate = useNavigate()

  useEffect(() => {
    apiFetch('/investigator/me')
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json()
          storeCsrfFromResponse(data)
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
