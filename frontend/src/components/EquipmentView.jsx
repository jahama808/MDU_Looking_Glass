import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import './EquipmentView.css'

function EquipmentView() {
  const [xponShelves, setXponShelves] = useState([])
  const [routers7x50, setRouters7x50] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('xpon')
  const [searchTerm, setSearchTerm] = useState('')
  const [tooltip, setTooltip] = useState({ show: false, text: '', x: 0, y: 0 })

  useEffect(() => {
    fetchEquipment()
  }, [])

  useEffect(() => {
    // Add event listeners to SVG elements for tooltips
    const handleMouseMove = (e) => {
      const target = e.target.closest('.device')
      if (target) {
        const tooltipText = target.getAttribute('data-tooltip')
        if (tooltipText) {
          const container = document.querySelector('.topology-content')
          if (container) {
            const rect = container.getBoundingClientRect()
            setTooltip({
              show: true,
              text: tooltipText,
              x: e.clientX - rect.left,
              y: e.clientY - rect.top
            })
          }
        }
      } else {
        setTooltip({ show: false, text: '', x: 0, y: 0 })
      }
    }

    const handleMouseLeave = () => {
      setTooltip({ show: false, text: '', x: 0, y: 0 })
    }

    // Wait for the object to load, then attach listeners to the SVG document
    const objectElement = document.querySelector('.topology-diagram-object')
    if (objectElement) {
      const attachListeners = () => {
        const svgDoc = objectElement.contentDocument
        if (svgDoc) {
          svgDoc.addEventListener('mousemove', handleMouseMove)
          svgDoc.addEventListener('mouseleave', handleMouseLeave)
        }
      }

      // If already loaded, attach immediately
      if (objectElement.contentDocument) {
        attachListeners()
      } else {
        // Otherwise wait for load event
        objectElement.addEventListener('load', attachListeners)
      }

      return () => {
        const svgDoc = objectElement.contentDocument
        if (svgDoc) {
          svgDoc.removeEventListener('mousemove', handleMouseMove)
          svgDoc.removeEventListener('mouseleave', handleMouseLeave)
        }
      }
    }
  }, [loading])

  const fetchEquipment = async () => {
    try {
      setLoading(true)
      const [xponResponse, routerResponse] = await Promise.all([
        axios.get('/api/xpon-shelves'),
        axios.get('/api/7x50s')
      ])
      setXponShelves(xponResponse.data)
      setRouters7x50(routerResponse.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch equipment data. Make sure the Flask API server is running.')
      console.error('Error fetching equipment:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredXponShelves = xponShelves.filter(shelf => {
    const lowerSearchTerm = searchTerm.toLowerCase()
    const nameMatch = shelf.shelf_name.toLowerCase().includes(lowerSearchTerm)
    const propertyMatch = shelf.property_names && shelf.property_names.toLowerCase().includes(lowerSearchTerm)
    return nameMatch || propertyMatch
  })

  const filteredRouters = routers7x50.filter(router => {
    const lowerSearchTerm = searchTerm.toLowerCase()
    const nameMatch = router.router_name.toLowerCase().includes(lowerSearchTerm)
    const propertyMatch = router.property_names && router.property_names.toLowerCase().includes(lowerSearchTerm)
    return nameMatch || propertyMatch
  })

  if (loading) {
    return <div className="loading">Loading equipment data...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="equipment-view">
      <div className="equipment-header">
        <h1>Network Equipment</h1>
        <div className="equipment-tabs">
          <button
            className={`tab ${activeTab === 'xpon' ? 'active' : ''}`}
            onClick={() => setActiveTab('xpon')}
          >
            xPON Shelves ({xponShelves.length})
          </button>
          <button
            className={`tab ${activeTab === '7x50' ? 'active' : ''}`}
            onClick={() => setActiveTab('7x50')}
          >
            7x50 Routers ({routers7x50.length})
          </button>
        </div>
      </div>

      {/* Topology Map Section */}
      <div className="topology-map-section">
        <div className="topology-header">
          <h2>Topology Map</h2>
        </div>
        <div className="topology-content" style={{ position: 'relative' }}>
          <object
            data="/fiber_network_architecture.svg"
            type="image/svg+xml"
            className="topology-diagram topology-diagram-object"
            aria-label="Fiber Network Architecture Topology"
          >
            Your browser does not support SVG
          </object>
          {tooltip.show && (
            <div
              className="topology-tooltip"
              style={{
                left: `${tooltip.x + 15}px`,
                top: `${tooltip.y + 15}px`
              }}
            >
              {tooltip.text}
            </div>
          )}
        </div>
      </div>

      <div className="search-section">
        <input
          type="text"
          placeholder={`Search ${activeTab === 'xpon' ? 'xPON shelves' : '7x50 routers'} by name or property...`}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {activeTab === 'xpon' && (
        <div className="equipment-section">
          <div className="equipment-count">
            Showing {filteredXponShelves.length} of {xponShelves.length} xPON shelves
          </div>
          <div className="equipment-grid">
            {filteredXponShelves.map((shelf) => (
              <Link
                to={`/xpon-shelf/${shelf.shelf_id}`}
                key={shelf.shelf_id}
                className="equipment-card"
              >
                <h3>{shelf.shelf_name}</h3>
                <div className="equipment-stats">
                  <div className="stat">
                    <span className="label">Properties:</span>
                    <span className="value">{shelf.total_properties}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Networks:</span>
                    <span className="value">{shelf.total_networks}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {filteredXponShelves.length === 0 && (
            <div className="no-results">
              No xPON shelves found matching "{searchTerm}"
            </div>
          )}
        </div>
      )}

      {activeTab === '7x50' && (
        <div className="equipment-section">
          <div className="equipment-count">
            Showing {filteredRouters.length} of {routers7x50.length} 7x50 routers
          </div>
          <div className="equipment-grid">
            {filteredRouters.map((router) => (
              <Link
                to={`/7x50/${router.router_id}`}
                key={router.router_id}
                className="equipment-card"
              >
                <h3>{router.router_name}</h3>
                <div className="equipment-stats">
                  <div className="stat">
                    <span className="label">Properties:</span>
                    <span className="value">{router.total_properties}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Networks:</span>
                    <span className="value">{router.total_networks}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {filteredRouters.length === 0 && (
            <div className="no-results">
              No 7x50 routers found matching "{searchTerm}"
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EquipmentView
