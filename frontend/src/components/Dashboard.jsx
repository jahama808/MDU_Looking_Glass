import { useState, useEffect } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [propertyWideOutages, setPropertyWideOutages] = useState(null)
  const [ongoingOutages, setOngoingOutages] = useState([])
  const [ongoingCount, setOngoingCount] = useState(0)
  const [analysis, setAnalysis] = useState(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)

      // Fetch required data
      const [statsRes, outagesRes] = await Promise.all([
        axios.get('/api/stats'),
        axios.get('/api/property-wide-outages')
      ])

      setStats(statsRes.data)
      setPropertyWideOutages(outagesRes.data)

      // Try to fetch ongoing outages (optional - may not exist in all databases)
      try {
        const [ongoingCountRes, ongoingOutagesRes] = await Promise.all([
          axios.get('/api/ongoing-outages/count'),
          axios.get('/api/ongoing-outages')
        ])
        setOngoingCount(ongoingCountRes.data.count)
        setOngoingOutages(ongoingOutagesRes.data)
      } catch (err) {
        console.log('Ongoing outages feature not available (table may not exist)')
        setOngoingCount(0)
        setOngoingOutages([])
      }

      // If property-wide outages detected, fetch AI analysis
      if (outagesRes.data.has_property_wide_outages) {
        fetchOutageAnalysis()
      }

      setError(null)
    } catch (err) {
      setError('Failed to fetch statistics. Make sure the Flask API server is running.')
      console.error('Error fetching stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchOutageAnalysis = async () => {
    try {
      setAnalysisLoading(true)
      const response = await axios.get('/api/dashboard/outage-analysis')
      setAnalysis(response.data)
    } catch (err) {
      console.error('Error fetching outage analysis:', err)
      setAnalysis({
        analysis: 'AI analysis unavailable.',
        error: err.message
      })
    } finally {
      setAnalysisLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading statistics...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Network Monitoring Summary</h1>
      </div>

      {/* Top Property Widget - Full Width */}
      {stats.top_property && (
        <div
          className="widget widget-full-width widget-clickable"
          onClick={() => navigate(`/property/${stats.top_property.id}`)}
          style={{ cursor: 'pointer' }}
        >
          <div className="widget-header">
            <h2>Most Affected Property (Past 24 Hours)</h2>
          </div>
          <div className="widget-content">
            <div className="top-property-info">
              <div className="property-name-large">{stats.top_property.name}</div>
              <div className="property-outage-count">{stats.top_property.outages}</div>
              <div className="property-outage-label">outages</div>
            </div>
          </div>
        </div>
      )}

      {/* Currently Down Networks Widget - Full Width */}
      {ongoingCount > 0 && (
        <div className="widget widget-warning widget-full-width">
          <div className="widget-header">
            <h2>🔴 Currently Down Networks</h2>
            <div className="widget-actions">
              <span className="alert-badge-warning">{ongoingCount}</span>
            </div>
          </div>
          <div className="widget-content">
            <div className="ongoing-outages-list two-column">
              {[...ongoingOutages].sort((a, b) => {
                // Sort alphabetically by property name
                const nameA = (a.property_name || '').toLowerCase()
                const nameB = (b.property_name || '').toLowerCase()
                return nameA.localeCompare(nameB)
              }).map((outage) => {
                const startTime = new Date(outage.wan_down_start)
                const duration = Math.floor((new Date() - startTime) / (1000 * 60 * 60)) // hours

                return (
                  <Link
                    key={outage.ongoing_outage_id}
                    to={`/network/${outage.network_id}`}
                    className="ongoing-outage-row"
                  >
                    <span className="status-dot ongoing"></span>
                    <div className="outage-info">
                      <div className="outage-property">{outage.property_name}</div>
                      <div className="outage-detail">
                        Network {Math.floor(outage.network_id)} • {outage.street_address} {outage.subloc || ''}
                      </div>
                      <div className="outage-duration">
                        Down for {duration}h • {outage.reason || 'Unknown reason'}
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Left Column */}
        <div className="dashboard-column">
          {/* Network Health Overview Widget */}
          <div className="widget">
            <div className="widget-header">
              <h2>Network Health Overview</h2>
              <div className="widget-actions">
                <Link to="/properties" className="widget-link">View All</Link>
              </div>
            </div>
            <div className="widget-content">
              <div className="health-summary">
                <div className="health-chart">
                  <div className="donut-chart">
                    <svg viewBox="0 0 100 100" className="donut">
                      {/* Background circle */}
                      <circle cx="50" cy="50" r="40" fill="none" stroke="#2d333b" strokeWidth="20"/>
                      {/* Green portion (Up networks) */}
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="#51cf66"
                        strokeWidth="20"
                        strokeDasharray={`${(stats.total_networks - stats.networks_with_outages) / stats.total_networks * 251.2} 251.2`}
                        transform="rotate(-90 50 50)"
                      />
                      {/* Red portion (Down networks) */}
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="#ff6b6b"
                        strokeWidth="20"
                        strokeDasharray={`${stats.networks_with_outages / stats.total_networks * 251.2} 251.2`}
                        strokeDashoffset={`-${(stats.total_networks - stats.networks_with_outages) / stats.total_networks * 251.2}`}
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="donut-center">
                      <div className="donut-value">{stats.total_networks}</div>
                      <div className="donut-label">Total</div>
                    </div>
                  </div>
                </div>
                <div className="health-stats">
                  <div className="health-stat">
                    <span className="stat-indicator up"></span>
                    <span className="stat-number">{stats.total_networks - stats.networks_with_outages}</span>
                    <span className="stat-label">Up</span>
                  </div>
                  <div className="health-stat">
                    <span className="stat-indicator down"></span>
                    <span className="stat-number">{stats.networks_with_outages}</span>
                    <span className="stat-label">Down</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Properties with Outages Widget */}
          {propertyWideOutages && propertyWideOutages.has_property_wide_outages && (
            <div className="widget widget-alert">
              <div className="widget-header">
                <h2>⚠️ Property-Wide Outages</h2>
                <div className="widget-actions">
                  <span className="alert-badge">{propertyWideOutages.count}</span>
                </div>
              </div>
              <div className="widget-content">
                <div className="property-list">
                  {propertyWideOutages.properties.map((property) => (
                    <Link
                      key={property.property_id}
                      to={`/property/${property.property_id}`}
                      className="property-row"
                    >
                      <span className="status-dot critical"></span>
                      <div className="property-info">
                        <div className="property-name">{property.property_name}</div>
                        <div className="property-detail">
                          {property.networks_with_outages} / {property.total_networks} networks • {new Date(property.outage_hour).toLocaleString()}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* AI Analysis Widget */}
          {propertyWideOutages && propertyWideOutages.has_property_wide_outages && (
            <div className="widget">
              <div className="widget-header">
                <h2>🤖 AI Root Cause Analysis</h2>
                {analysis && analysis.model && (
                  <div className="widget-actions">
                    <span className="model-badge">{analysis.model}</span>
                  </div>
                )}
              </div>
              <div className="widget-content">
                {analysisLoading && (
                  <div className="analysis-loading">
                    <div className="spinner"></div>
                    <p>Analyzing outage patterns...</p>
                  </div>
                )}
                {!analysisLoading && analysis && (
                  <div className="analysis-content">
                    {analysis.error ? (
                      <div className="analysis-error">⚠️ {analysis.analysis}</div>
                    ) : (
                      <div className="analysis-text">
                        {analysis.analysis.split('\n').map((line, idx) => (
                          <p key={idx}>{line}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="dashboard-column">
          {/* Statistics Summary Widget */}
          <div className="widget">
            <div className="widget-header">
              <h2>Outage Statistics</h2>
              <div className="widget-actions">
                <span className="widget-link">Last 24h</span>
              </div>
            </div>
            <div className="widget-content">
              <table className="stats-table">
                <tbody>
                  <tr>
                    <td className="stat-label">Properties with Outages</td>
                    <td className="stat-value">{stats.properties_with_outages}</td>
                  </tr>
                  <tr>
                    <td className="stat-label">Total Outages</td>
                    <td className="stat-value critical">{stats.total_outages}</td>
                  </tr>
                  <tr>
                    <td className="stat-label">Total Networks</td>
                    <td className="stat-value">{stats.total_networks}</td>
                  </tr>
                  <tr>
                    <td className="stat-label">Networks with Outages</td>
                    <td className="stat-value warning">{stats.networks_with_outages}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Outage Reasons Widget */}
          {stats.outage_reasons && Object.keys(stats.outage_reasons).length > 0 && (() => {
            const reasons = Object.keys(stats.outage_reasons);
            if (reasons.length === 1) {
              const singleReason = reasons[0];
              if (!singleReason || singleReason.trim() === '' || singleReason.toUpperCase() === 'UNKNOWN') {
                return false;
              }
            }
            const hasValidReasons = reasons.some(reason =>
              reason && reason.trim() !== '' && reason.toUpperCase() !== 'UNKNOWN'
            );
            return hasValidReasons;
          })() && (
            <div className="widget">
              <div className="widget-header">
                <h2>Outage Reasons</h2>
              </div>
              <div className="widget-content">
                <table className="reasons-table">
                  <tbody>
                    {Object.entries(stats.outage_reasons).map(([reason, count]) => (
                      <tr key={reason}>
                        <td className="reason-label">{reason || 'UNKNOWN'}</td>
                        <td className="reason-value">{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
