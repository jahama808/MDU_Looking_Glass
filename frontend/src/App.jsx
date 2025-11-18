import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import Dashboard from './components/Dashboard'
import PropertyList from './components/PropertyList'
import PropertyDetail from './components/PropertyDetail'
import NetworkDetail from './components/NetworkDetail'
import EquipmentView from './components/EquipmentView'
import XponShelfDetail from './components/XponShelfDetail'
import Router7x50Detail from './components/Router7x50Detail'
import SpeedtestPerformance from './components/SpeedtestPerformance'
import SpeedtestTable from './components/SpeedtestTable'

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <nav>
            <Link to="/" className="logo">Property Outage Dashboard</Link>
            <div className="nav-links">
              <Link to="/">Dashboard</Link>
              <Link to="/properties">Properties</Link>
              <Link to="/equipment">Equipment</Link>
              <Link to="/speedtest">Speedtest</Link>
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
          </Routes>
        </main>

        <footer className="app-footer">
          <p>Property Outage Monitoring System</p>
        </footer>
      </div>
    </Router>
  )
}

export default App
