import { NavLink, Route, Routes } from 'react-router-dom'
import { ControlPage } from './pages/ControlPage'
import { SchedulePage } from './pages/SchedulePage'
import './App.css'

export default function App() {
  return (
    <div className="app-shell">
      <nav className="top-nav">
        <span className="brand">BBP</span>
        <NavLink to="/" end>
          Schedule
        </NavLink>
        <NavLink to="/control">Control</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<SchedulePage />} />
        <Route path="/schedule" element={<SchedulePage />} />
        <Route path="/control" element={<ControlPage />} />
      </Routes>
    </div>
  )
}
