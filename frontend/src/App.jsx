import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import PropertyList from './components/PropertyList'
import PropertyDetail from './components/PropertyDetail'
import NetworkDetail from './components/NetworkDetail'
import EquipmentView from './components/EquipmentView'
import XponShelfDetail from './components/XponShelfDetail'
import Router7x50Detail from './components/Router7x50Detail'
import SpeedtestPerformance from './components/SpeedtestPerformance'
import SpeedtestTable from './components/SpeedtestTable'
import AdminPortal from './components/AdminPortal'

function AppContent() {
  const { authenticated, loading, user, login, logout } = useAuth()

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  if (!authenticated) {
    return <Login onLogin={login} />
  }

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <nav>
            <Link to="/" className="logo">MDU Performance Dashboard</Link>
            <div className="nav-links">
              <Link to="/">Dashboard</Link>
              <Link to="/properties">Properties</Link>
              <Link to="/equipment">Equipment</Link>
              <Link to="/speedtest">Speedtest</Link>
            </div>
            <div className="user-menu">
              {user?.role === 'admin' && (
                <Link to="/admin" className="user-role-badge">Admin</Link>
              )}
              <button onClick={logout} className="logout-button">
                Logout
              </button>
            </div>
          </nav>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/properties" element={<PropertyList />} />
            <Route path="/property/:id" element={<PropertyDetail />} />
            <Route path="/network/:id" element={<NetworkDetail />} />
            <Route path="/equipment" element={<EquipmentView />} />
            <Route path="/xpon-shelf/:id" element={<XponShelfDetail />} />
            <Route path="/7x50/:id" element={<Router7x50Detail />} />
            <Route path="/speedtest" element={<SpeedtestPerformance />} />
            <Route path="/speedtest-table" element={<SpeedtestTable />} />
            <Route path="/admin" element={<AdminPortal />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>Koko Crater Labs</p>
        </footer>
      </div>
    </Router>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
