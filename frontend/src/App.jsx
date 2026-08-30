import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

import Home from './pages/Home'
import AdminGuard from './pages/AdminGuard'
import AdminLogin from './pages/AdminLogin'
import AdminHome from './pages/AdminHome'

function App() {
  return (
    <Routes>
      {/* Public — system status / first-run setup */}
      <Route path="/" element={<Home />} />

      {/* Admin area */}
      <Route path="/admin" element={<AdminGuard />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/home" element={<AdminHome />} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
