import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import './PropertyList.css'

function PropertyList() {
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIsland, setSelectedIsland] = useState('')

  useEffect(() => {
    fetchProperties()
  }, [])

  const fetchProperties = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/properties')
      setProperties(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch properties. Make sure the Flask API server is running.')
      console.error('Error fetching properties:', err)
    } finally {
      setLoading(false)
    }
  }

  // Get unique islands for dropdown
  const islands = [...new Set(properties.map(p => p.island).filter(Boolean))].sort()

  const filteredProperties = properties.filter(property => {
    const matchesSearch = property.property_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesIsland = !selectedIsland || property.island === selectedIsland
    return matchesSearch && matchesIsland
  })

  if (loading) {
    return <div className="loading">Loading properties...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="property-list">
      <div className="property-list-header">
        <h1>Properties with Outages</h1>
        <div className="filters-row">
          <input
            type="text"
            placeholder="Search properties..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <select
            value={selectedIsland}
            onChange={(e) => setSelectedIsland(e.target.value)}
            className="island-dropdown"
          >
            <option value="">All Islands</option>
            {islands.map(island => (
              <option key={island} value={island}>{island}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="property-count">
        Showing {filteredProperties.length} of {properties.length} properties
        {selectedIsland && <span className="island-filter"> on {selectedIsland}</span>}
      </div>

      <div className="properties-grid">
        {filteredProperties.map((property) => (
          <Link
            to={`/property/${property.property_id}`}
            key={property.property_id}
            className="property-card"
          >
            <h3>
              {property.property_name}
              {property.island && (
                <span className="property-island">{property.island}</span>
              )}
            </h3>
            <div className="property-stats">
              <div className="stat">
                <span className="label">Networks</span>
                <span className="value">{property.total_networks}</span>
              </div>
              <div className="stat">
                <span className="label">Outages (24h)</span>
                <span className="value outage-count">{property.total_outages}</span>
              </div>
            </div>
            {property.last_updated && (
              <div className="last-updated">
                Updated: {new Date(property.last_updated).toLocaleString()}
              </div>
            )}
          </Link>
        ))}
      </div>

      {filteredProperties.length === 0 && (
        <div className="no-results">
          No properties found matching "{searchTerm}"
        </div>
      )}
    </div>
  )
}

export default PropertyList
