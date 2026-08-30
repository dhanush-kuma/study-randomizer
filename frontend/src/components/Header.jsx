import { NavLink } from 'react-router-dom'

function Header({ children }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <NavLink to="/" className="site-name">
          Study Randomizer
        </NavLink>
        <nav className="nav-menu">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Home
          </NavLink>
          <NavLink
            to="/admin"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Admin
          </NavLink>
          <NavLink
            to="/organizer"
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            Organizer
          </NavLink>
        </nav>
      </div>
      {children}
    </header>
  )
}

export default Header
