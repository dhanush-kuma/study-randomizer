import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch from backend')
        return res.json()
      })
      .then((data) => setMessage(data.message))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="app">
      <h1>Open Source Study Randomizer</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && <p className="message">{message}</p>}
    </main>
  )
}

export default App
