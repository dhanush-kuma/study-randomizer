import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

import Home from './pages/Home'
import AdminGuard from './pages/AdminGuard'
import AdminLogin from './pages/AdminLogin'
import AdminHome from './pages/AdminHome'
import OrganizerGuard from './pages/OrganizerGuard'
import OrganizerLogin from './pages/OrganizerLogin'
import OrganizerHome from './pages/OrganizerHome'
import CreateStudy from './pages/CreateStudy'

function App() {
  return (
    <Routes>
      {/* Public — system status / first-run setup */}
      <Route path="/" element={<Home />} />

      {/* Admin area */}
      <Route path="/admin" element={<AdminGuard />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/home" element={<AdminHome />} />

      {/* Organizer area */}
      <Route path="/organizer" element={<OrganizerGuard />} />
      <Route path="/organizer/login" element={<OrganizerLogin />} />
      <Route path="/organizer/home" element={<OrganizerHome />} />
      <Route path="/organizer/studies/new" element={<CreateStudy />} />


      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}


export default App
