import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './SpeedtestTable.css'

function SpeedtestTable() {
  const navigate = useNavigate()
  const [performanceData, setPerformanceData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [islandFilter, setIslandFilter] = useState('All')
  const [sortConfig, setSortConfig] = useState({ key: 'download.pass_percentage', direction: 'asc' })

  useEffect(() => {
    fetchPerformanceData()
  }, [])

  const fetchPerformanceData = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/speedtest-performance-table')
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

  // Filter and sort data
  const filteredData = performanceData
    .filter(property => {
      const matchesSearch = property.property_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesIsland = islandFilter === 'All' || property.island === islandFilter
      return matchesSearch && matchesIsland
    })
    .sort((a, b) => {
      let aValue, bValue

      // Handle nested values (e.g., 'download.pass_percentage')
      if (sortConfig.key.includes('.')) {
        const keys = sortConfig.key.split('.')
        aValue = a[keys[0]][keys[1]]
        bValue = b[keys[0]][keys[1]]
      } else {
        aValue = a[sortConfig.key]
        bValue = b[sortConfig.key]
      }

      // Handle string vs number comparison
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase()
        bValue = bValue.toLowerCase()
      }

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })

  const handleSort = (key) => {
    setSortConfig({
      key,
      direction: sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    })
  }

  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return '⇅'
    return sortConfig.direction === 'asc' ? '↑' : '↓'
  }

  // Calculate distribution statistics for filtered data
  const calculateDistribution = (data, type) => {
    const tiers = [
      { range: '90-100%', min: 90, max: 100, count: 0 },
      { range: '80-90%', min: 80, max: 90, count: 0 },
      { range: '70-80%', min: 70, max: 80, count: 0 },
      { range: '60-70%', min: 60, max: 70, count: 0 },
      { range: '50-60%', min: 50, max: 60, count: 0 },
      { range: 'Below 50%', min: 0, max: 50, count: 0 }
    ]

    data.forEach(property => {
      const percentage = property[type].pass_percentage
      for (let tier of tiers) {
        if (percentage >= tier.min && percentage < tier.max) {
          tier.count++
          break
        }
        // Handle 100% edge case
        if (percentage === 100 && tier.max === 100) {
          tier.count++
          break
        }
      }
    })

    return tiers
  }

  const downloadDistribution = calculateDistribution(filteredData, 'download')
  const uploadDistribution = calculateDistribution(filteredData, 'upload')

  if (loading) {
    return <div className="loading">Loading speedtest performance data...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="speedtest-table-page">
      <div className="speedtest-header">
        <h1>Speedtest Performance Table</h1>

        <div className="info-box">
          <div className="info-icon">ℹ️</div>
          <div className="info-content">
            Pass/Fail performance is based on the results achieved by the integrated eero speedtest compared against the provisioned service for a given network. A network that achieves a speedtest result that is 85% or better than the provisioned speed is considered a pass.
          </div>
        </div>

        <div className="view-toggle-container">
          <button
            className="view-toggle-btn"
            onClick={() => navigate('/speedtest')}
          >
            Card View
          </button>
          <button
            className={`view-toggle-btn active`}
            onClick={() => {}}
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
            value={islandFilter}
            onChange={(e) => setIslandFilter(e.target.value)}
            className="island-filter"
          >
            {islands.map(island => (
              <option key={island} value={island}>{island}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Statistics Section */}
      <div className="statistics-section">
        <h2>Performance Distribution Statistics</h2>
        <p className="stats-subtitle">
          Distribution of properties by pass percentage tiers
          {islandFilter !== 'All' && <span className="island-filter-label"> for {islandFilter}</span>}
        </p>

        <div className="statistics-grid">
          <div className="stat-chart">
            <h3>Download Performance Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={downloadDistribution} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" angle={-45} textAnchor="end" height={80} />
                <YAxis label={{ value: 'Properties', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#2196F3" name="Properties" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="stat-chart">
            <h3>Upload Performance Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={uploadDistribution} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" angle={-45} textAnchor="end" height={80} />
                <YAxis label={{ value: 'Properties', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#4CAF50" name="Properties" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="property-count">
        Showing {filteredData.length} of {performanceData.length} properties with speedtest data
        {islandFilter !== 'All' && <span className="island-filter-label"> on {islandFilter}</span>}
      </div>

      {filteredData.length === 0 && (
        <div className="no-results">
          No properties found matching your criteria
        </div>
      )}

      {filteredData.length > 0 && (
        <div className="table-container">
          <table className="speedtest-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('property_name')} className="sortable">
                  Property {getSortIndicator('property_name')}
                </th>
                <th onClick={() => handleSort('island')} className="sortable">
                  Island {getSortIndicator('island')}
                </th>
                <th className="equipment-col">xPON OLT</th>
                <th className="equipment-col">7x50 Router</th>
                <th onClick={() => handleSort('download.tests_passing')} className="sortable numeric">
                  DL Pass {getSortIndicator('download.tests_passing')}
                </th>
                <th onClick={() => handleSort('download.tests_failing')} className="sortable numeric">
                  DL Fail {getSortIndicator('download.tests_failing')}
                </th>
                <th onClick={() => handleSort('download.pass_percentage')} className="sortable numeric">
                  DL Pass % {getSortIndicator('download.pass_percentage')}
                </th>
                <th onClick={() => handleSort('upload.tests_passing')} className="sortable numeric">
                  UL Pass {getSortIndicator('upload.tests_passing')}
                </th>
                <th onClick={() => handleSort('upload.tests_failing')} className="sortable numeric">
                  UL Fail {getSortIndicator('upload.tests_failing')}
                </th>
                <th onClick={() => handleSort('upload.pass_percentage')} className="sortable numeric">
                  UL Pass % {getSortIndicator('upload.pass_percentage')}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((property) => (
                <tr key={property.property_id}>
                  <td className="property-name">
                    <Link to={`/property/${property.property_id}`}>
                      {property.property_name}
                    </Link>
                  </td>
                  <td>{property.island || 'N/A'}</td>
                  <td className="equipment-col" title={property.xpon_shelves}>
                    {property.xpon_shelves}
                  </td>
                  <td className="equipment-col" title={property.routers_7x50}>
                    {property.routers_7x50}
                  </td>
                  <td className="numeric">{property.download.tests_passing}</td>
                  <td className="numeric fail">{property.download.tests_failing}</td>
                  <td className={`numeric percent ${getPercentageClass(property.download.pass_percentage)}`}>
                    {property.download.pass_percentage}%
                  </td>
                  <td className="numeric">{property.upload.tests_passing}</td>
                  <td className="numeric fail">{property.upload.tests_failing}</td>
                  <td className={`numeric percent ${getPercentageClass(property.upload.pass_percentage)}`}>
                    {property.upload.pass_percentage}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function getPercentageClass(percentage) {
  if (percentage >= 90) return 'excellent'
  if (percentage >= 75) return 'good'
  if (percentage >= 50) return 'fair'
  return 'poor'
}

export default SpeedtestTable
