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
import StudyInvites from './pages/StudyInvites'
import StudyHome from './pages/StudyHome'
import StudyArms from './pages/StudyArms'
import StudyRandomization from './pages/StudyRandomization'
import UploadCSV from './pages/UploadCSV'
import DoctorGuard from './pages/DoctorGuard'
import DoctorLogin from './pages/DoctorLogin'
import DoctorSignup from './pages/DoctorSignup'
import DoctorHome from './pages/DoctorHome'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />

      <Route path="/admin" element={<AdminGuard />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/home" element={<AdminHome />} />

      <Route path="/organizer" element={<OrganizerGuard />} />
      <Route path="/organizer/login" element={<OrganizerLogin />} />
      <Route path="/organizer/home" element={<OrganizerHome />} />
      <Route path="/organizer/studies/new" element={<CreateStudy />} />
      <Route path="/organizer/studies/:studyId/home" element={<StudyHome />} />
      <Route path="/organizer/studies/:studyId/arms" element={<StudyArms />} />
      <Route path="/organizer/studies/:studyId/randomization" element={<StudyRandomization />} />
      <Route path="/organizer/studies/:studyId/upload-csv" element={<UploadCSV />} />
      <Route path="/organizer/studies/:studyId/invites" element={<StudyInvites />} />

      <Route path="/doctor" element={<DoctorGuard />} />
      <Route path="/doctor/login" element={<DoctorLogin />} />
      <Route path="/doctor/signup" element={<DoctorSignup />} />
      <Route path="/doctor/home" element={<DoctorHome />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
