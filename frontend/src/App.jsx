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
import StudyInvestigators from './pages/StudyInvestigators'
import StudyHome from './pages/StudyHome'
import StudyArms from './pages/StudyArms'
import StudyRandomization from './pages/StudyRandomization'
import UploadCSV from './pages/UploadCSV'
import InvestigatorGuard from './pages/InvestigatorGuard'
import InvestigatorLogin from './pages/InvestigatorLogin'
import InvestigatorHome from './pages/InvestigatorHome'
import InvestigatorChangePassword from './pages/InvestigatorChangePassword'

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
      <Route path="/organizer/studies/:studyId/investigators" element={<StudyInvestigators />} />

      <Route path="/investigator" element={<InvestigatorGuard />} />
      <Route path="/investigator/login" element={<InvestigatorLogin />} />
      <Route path="/investigator/home" element={<InvestigatorHome />} />
      <Route path="/investigator/change-password" element={<InvestigatorChangePassword />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
