import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import './SpeedtestPerformance.css'

function SpeedtestPerformance() {
  const navigate = useNavigate()
  const [performanceData, setPerformanceData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIsland, setSelectedIsland] = useState('All')

  useEffect(() => {
    fetchPerformanceData()
  }, [])

  const fetchPerformanceData = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/speedtest-performance')
      setPerformanceData(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch speedtest performance data. Make sure the Flask API server is running.')
      console.error('Error fetching speedtest performance:', err)
    } finally {
      setLoading(false)
    }
  }

  // Get unique islands for filter
  const islands = ['All', ...new Set(performanceData.map(p => p.island).filter(Boolean))]

  const filteredData = performanceData
    .filter(property => {
      const matchesSearch = property.property_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesIsland = selectedIsland === 'All' || property.island === selectedIsland
      return matchesSearch && matchesIsland
    })
    .sort((a, b) => {
      // Sort by download pass percentage (lowest first)
      // If download pass percentage is the same, sort by upload pass percentage
      if (a.download.pass_percentage !== b.download.pass_percentage) {
        return a.download.pass_percentage - b.download.pass_percentage
      }
      return a.upload.pass_percentage - b.upload.pass_percentage
    })

  if (loading) {
    return <div className="loading">Loading speedtest performance data...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="speedtest-performance">
      <div className="speedtest-header">
        <h1>Speedtest Performance by Property</h1>
        <p className="subtitle">
          Showing networks with actual speeds at 85% or higher of target speeds vs below 85%
        </p>

        <div className="view-toggle-container">
          <button
            className={`view-toggle-btn active`}
            onClick={() => {}}
          >
            Card View
          </button>
          <button
            className="view-toggle-btn"
            onClick={() => navigate('/speedtest-table')}
          >
            Table View
          </button>
        </div>

        <div className="controls">
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
            className="island-filter"
          >
            {islands.map(island => (
              <option key={island} value={island}>{island}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="property-count">
        Showing {filteredData.length} of {performanceData.length} properties with speedtest data
        {selectedIsland !== 'All' && <span className="island-filter-label"> on {selectedIsland}</span>}
      </div>

      {filteredData.length === 0 && (
        <div className="no-results">
          No properties found matching "{searchTerm}"
        </div>
      )}

      <div className="performance-grid">
        {filteredData.map((property) => (
          <div key={property.property_id} className="property-performance-card">
            <h3>
              <Link to={`/property/${property.property_id}`} className="property-link">
                {property.property_name}
              </Link>
            </h3>
            {property.island && (
              <div className="property-island">{property.island}</div>
            )}
            <div className="property-info">
              <span>Total Networks: {property.total_networks}</span>
            </div>

            {/* Download Performance */}
            {property.download.tests_total > 0 && (
              <div className="performance-section">
                <h4>Download Performance</h4>
                <div className="performance-table">
                  <div className="performance-row header">
                    <div className="performance-cell">Metric</div>
                    <div className="performance-cell">Count</div>
                    <div className="performance-cell">Percentage</div>
                  </div>
                  <div className="performance-row passing">
                    <div className="performance-cell">Passing (≥85%)</div>
                    <div className="performance-cell value">{property.download.tests_passing}</div>
                    <div className="performance-cell value">
                      {property.download.tests_total > 0
                        ? Math.round((property.download.tests_passing / property.download.tests_total) * 100)
                        : 0}%
                    </div>
                  </div>
                  <div className="performance-row failing">
                    <div className="performance-cell">Failing (&lt;85%)</div>
                    <div className="performance-cell value">{property.download.tests_failing}</div>
                    <div className="performance-cell value">
                      {property.download.tests_total > 0
                        ? Math.round((property.download.tests_failing / property.download.tests_total) * 100)
                        : 0}%
                    </div>
                  </div>
                  <div className="performance-row total">
                    <div className="performance-cell">Total Tests</div>
                    <div className="performance-cell value">{property.download.tests_total}</div>
                    <div className="performance-cell value"></div>
                  </div>
                </div>
              </div>
            )}

            {/* Upload Performance */}
            {property.upload.tests_total > 0 && (
              <div className="performance-section">
                <h4>Upload Performance</h4>
                <div className="performance-table">
                  <div className="performance-row header">
                    <div className="performance-cell">Metric</div>
                    <div className="performance-cell">Count</div>
                    <div className="performance-cell">Percentage</div>
                  </div>
                  <div className="performance-row passing">
                    <div className="performance-cell">Passing (≥85%)</div>
                    <div className="performance-cell value">{property.upload.tests_passing}</div>
                    <div className="performance-cell value">
                      {property.upload.tests_total > 0
                        ? Math.round((property.upload.tests_passing / property.upload.tests_total) * 100)
                        : 0}%
                    </div>
                  </div>
                  <div className="performance-row failing">
                    <div className="performance-cell">Failing (&lt;85%)</div>
                    <div className="performance-cell value">{property.upload.tests_failing}</div>
                    <div className="performance-cell value">
                      {property.upload.tests_total > 0
                        ? Math.round((property.upload.tests_failing / property.upload.tests_total) * 100)
                        : 0}%
                    </div>
                  </div>
                  <div className="performance-row total">
                    <div className="performance-cell">Total Tests</div>
                    <div className="performance-cell value">{property.upload.tests_total}</div>
                    <div className="performance-cell value"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default SpeedtestPerformance
