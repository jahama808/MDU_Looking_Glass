import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './PropertyDetail.css'

function PropertyDetail() {
  const { id } = useParams()
  const [property, setProperty] = useState(null)
  const [hourlyData, setHourlyData] = useState([])
  const [hourly7DaysData, setHourly7DaysData] = useState([])
  const [networks, setNetworks] = useState([])
  const [ongoingOutages, setOngoingOutages] = useState([])
  const [xponShelves, setXponShelves] = useState([])
  const [routers7x50, setRouters7x50] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Helper function to format speedtest data
  const formatSpeedtest = (actual, target) => {
    if (!actual || !target) {
      return { display: 'N/A', passing: null }
    }
    const threshold = target * 0.85
    const passing = actual >= threshold
    const percentage = ((actual / target) * 100).toFixed(0)
    return {
      display: `${actual.toFixed(1)} / ${target.toFixed(0)} (${percentage}%)`,
      passing,
      actual,
      target
    }
  }

  useEffect(() => {
    fetchPropertyData()
  }, [id])

  const fetchPropertyData = async () => {
    try {
      setLoading(true)

      // Fetch required data
      const [propertyRes, hourlyRes, hourly7DaysRes, networksRes] = await Promise.all([
        axios.get(`/api/property/${id}`),
        axios.get(`/api/property/${id}/hourly`),
        axios.get(`/api/property/${id}/hourly-7days`),
        axios.get(`/api/property/${id}/networks`)
      ])

      setProperty(propertyRes.data.property)
      setXponShelves(propertyRes.data.xpon_shelves || [])
      setRouters7x50(propertyRes.data.routers_7x50 || [])

      // Try to fetch ongoing outages (optional - may not exist in all databases)
      let ongoingData = []
      try {
        const ongoingRes = await axios.get(`/api/property/${id}/ongoing-outages`)
        ongoingData = ongoingRes.data
        setOngoingOutages(ongoingData)
      } catch (err) {
        console.log('Ongoing outages feature not available')
        setOngoingOutages([])
      }

      // Format hourly data for chart
      const formattedHourly = hourlyRes.data.map(item => {
        const date = new Date(item.outage_hour)
        return {
          time: date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            hour12: false
          }),
          fullTime: date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }),
          outages: item.total_outage_count,
          ongoingOutages: 0
        }
      })

      // Add ongoing outages as current data point if there are any
      if (ongoingData.length > 0 && formattedHourly.length > 0) {
        const now = new Date()
        formattedHourly.push({
          time: now.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            hour12: false
          }),
          fullTime: now.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }),
          outages: 0,
          ongoingOutages: ongoingData.length
        })
      }

      setHourlyData(formattedHourly)

      // Format 7-day hourly data for chart
      const formatted7Days = hourly7DaysRes.data.map(item => {
        const date = new Date(item.outage_hour)
        return {
          time: date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            hour12: false
          }),
          fullTime: date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }),
          outages: item.total_outage_count,
          ongoingOutages: 0
        }
      })

      // Add ongoing outages as current data point if there are any
      if (ongoingRes.data.length > 0 && formatted7Days.length > 0) {
        const now = new Date()
        formatted7Days.push({
          time: now.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            hour12: false
          }),
          fullTime: now.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }),
          outages: 0,
          ongoingOutages: ongoingRes.data.length
        })
      }

      setHourly7DaysData(formatted7Days)

      setNetworks(networksRes.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch property details. Make sure the Flask API server is running.')
      console.error('Error fetching property data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading property details...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!property) {
    return <div className="error">Property not found</div>
  }

  return (
    <div className="property-detail">
      <div className="breadcrumb">
        <Link to="/properties">← Back to Properties</Link>
      </div>

      <div className="property-header">
        <h1>{property.property_name}</h1>
        <div className="property-summary">
          <div className="summary-item">
            <span className="label">Total Networks:</span>
            <span className="value">{property.total_networks}</span>
          </div>
          <div className="summary-item">
            <span className="label">Total Outages:</span>
            <span className="value">{property.total_outages}</span>
          </div>
          {property.last_updated && (
            <div className="summary-item">
              <span className="label">Last Updated:</span>
              <span className="value">{new Date(property.last_updated).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>

      {(xponShelves.length > 0 || routers7x50.length > 0) && (
        <div className="equipment-section">
          <h2>Network Equipment</h2>
          <div className="equipment-grid">
            {xponShelves.length > 0 && (
              <div className="equipment-category">
                <h3>xPON Shelves ({xponShelves.length})</h3>
                <div className="equipment-list">
                  {xponShelves.map((shelf) => (
                    <Link
                      key={shelf.shelf_id}
                      to={`/xpon-shelf/${shelf.shelf_id}`}
                      className="equipment-item"
                    >
                      <div className="equipment-name">{shelf.shelf_name}</div>
                      <div className="equipment-count">
                        {shelf.network_count} {shelf.network_count === 1 ? 'network' : 'networks'}
                      </div>
                      {(shelf.slots || shelf.pons) && (
                        <div className="equipment-details">
                          {shelf.slots && <div>Slots: {shelf.slots}</div>}
                          {shelf.pons && <div>PONs: {shelf.pons}</div>}
                        </div>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {routers7x50.length > 0 && (
              <div className="equipment-category">
                <h3>7x50 Routers ({routers7x50.length})</h3>
                <div className="equipment-list">
                  {routers7x50.map((router) => (
                    <Link
                      key={router.router_id}
                      to={`/7x50/${router.router_id}`}
                      className="equipment-item"
                    >
                      <div className="equipment-name">{router.router_name}</div>
                      <div className="equipment-count">
                        {router.network_count} {router.network_count === 1 ? 'network' : 'networks'}
                      </div>
                      {router.saps && (
                        <div className="equipment-details">
                          SAP: {router.saps}
                        </div>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {hourlyData.length > 0 && (
        <div className="chart-section">
          <h2>Hourly Outage Trend (Last 24 Hours)</h2>
          <p>
            Showing {hourlyData.length} hours of data
            {hourlyData.length > 0 && ` from ${hourlyData[0].time} to ${hourlyData[hourlyData.length - 1].time}`}
          </p>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3d444d" />
              <XAxis
                dataKey="time"
                angle={-45}
                textAnchor="end"
                height={100}
                interval="preserveStartEnd"
                minTickGap={5}
                stroke="#8b92a6"
                tick={{ fill: '#8b92a6' }}
              />
              <YAxis stroke="#8b92a6" tick={{ fill: '#8b92a6' }} />
              <Tooltip
                labelFormatter={(value, payload) => {
                  if (payload && payload.length > 0) {
                    return payload[0].payload.fullTime || value
                  }
                  return value
                }}
                contentStyle={{ backgroundColor: '#22272e', border: '1px solid #3d444d', borderRadius: '4px' }}
                labelStyle={{ color: '#e0e0e0' }}
                itemStyle={{ color: '#e0e0e0' }}
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Line
                type="monotone"
                dataKey="outages"
                stroke="#5dade2"
                strokeWidth={2}
                name="Outages (24h)"
                dot={{ r: 3, fill: '#5dade2' }}
                activeDot={{ r: 5, fill: '#3498db' }}
              />
              <Line
                type="monotone"
                dataKey="ongoingOutages"
                stroke="#ffa500"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Ongoing Outages"
                dot={{ r: 4, fill: '#ffa500' }}
                activeDot={{ r: 6, fill: '#ff8800' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {hourly7DaysData.length > 0 && (
        <div className="chart-section">
          <h2>7-Day Hourly Outage Trend</h2>
          <p>
            Showing {hourly7DaysData.length} hours of data
            {hourly7DaysData.length > 0 && ` from ${hourly7DaysData[0].time} to ${hourly7DaysData[hourly7DaysData.length - 1].time}`}
          </p>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={hourly7DaysData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3d444d" />
              <XAxis
                dataKey="time"
                angle={-45}
                textAnchor="end"
                height={100}
                interval="preserveStartEnd"
                minTickGap={5}
                stroke="#8b92a6"
                tick={{ fill: '#8b92a6' }}
              />
              <YAxis stroke="#8b92a6" tick={{ fill: '#8b92a6' }} />
              <Tooltip
                labelFormatter={(value, payload) => {
                  if (payload && payload.length > 0) {
                    return payload[0].payload.fullTime || value
                  }
                  return value
                }}
                contentStyle={{ backgroundColor: '#22272e', border: '1px solid #3d444d', borderRadius: '4px' }}
                labelStyle={{ color: '#e0e0e0' }}
                itemStyle={{ color: '#e0e0e0' }}
              />
              <Legend wrapperStyle={{ color: '#e0e0e0' }} />
              <Line
                type="monotone"
                dataKey="outages"
                stroke="#51cf66"
                strokeWidth={2}
                name="Outages (Last 7 Days)"
                dot={{ r: 3, fill: '#51cf66' }}
                activeDot={{ r: 5, fill: '#37b24d' }}
              />
              <Line
                type="monotone"
                dataKey="ongoingOutages"
                stroke="#ffa500"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Ongoing Outages"
                dot={{ r: 4, fill: '#ffa500' }}
                activeDot={{ r: 6, fill: '#ff8800' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {ongoingOutages.length > 0 && (
        <div className="ongoing-outages-section">
          <h2>🔴 Currently Down Networks ({ongoingOutages.length})</h2>
          <div className="ongoing-outages-alert">
            <strong>Active Outages:</strong> {ongoingOutages.length} network{ongoingOutages.length !== 1 ? 's are' : ' is'} currently experiencing outages.
          </div>
          <div className="ongoing-networks-table">
            <table>
              <thead>
                <tr>
                  <th>Network ID</th>
                  <th>Address</th>
                  <th>Unit</th>
                  <th>Customer</th>
                  <th>Start Time</th>
                  <th>Duration</th>
                  <th>Reason</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {ongoingOutages.map((outage) => {
                  const startTime = new Date(outage.wan_down_start)
                  const duration = Math.floor((new Date() - startTime) / (1000 * 60 * 60)) // hours

                  return (
                    <tr key={outage.ongoing_outage_id} className="ongoing-outage-row">
                      <td>
                        <a
                          href={`https://insight.eero.com/networks/${Math.floor(outage.network_id)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {Math.floor(outage.network_id)}
                        </a>
                        <span className="ongoing-indicator">LIVE</span>
                      </td>
                      <td>{outage.street_address || 'N/A'}</td>
                      <td>{outage.subloc || 'N/A'}</td>
                      <td>{outage.customer_name || 'N/A'}</td>
                      <td>{startTime.toLocaleString()}</td>
                      <td style={{ color: '#ffa500', fontWeight: '500' }}>{duration}h</td>
                      <td>{outage.reason || 'Unknown'}</td>
                      <td>
                        <Link to={`/network/${outage.network_id}`} className="btn btn-small">
                          View Details
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="networks-section">
        <h2>Networks ({networks.length})</h2>
        {networks.filter(n => n.is_chronic_problem).length > 0 && (
          <div className="chronic-networks-alert">
            <strong>⚠️ Chronic Problem Networks Detected:</strong> {networks.filter(n => n.is_chronic_problem).length} network(s)
            with more than 8 outages in the last 24 hours are highlighted below.
          </div>
        )}
        {networks.length > 0 ? (
          <div className="networks-table">
            <table>
              <thead>
                <tr>
                  <th>Network ID</th>
                  <th>Address</th>
                  <th>Unit</th>
                  <th>Customer</th>
                  <th>Download (Mbps)</th>
                  <th>Upload (Mbps)</th>
                  <th>Total Outages</th>
                  <th>24h Outages</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {networks.map((network) => (
                  <tr
                    key={network.network_id}
                    className={network.is_chronic_problem ? 'chronic-problem-network' : ''}
                  >
                    <td>
                      <a
                        href={`https://insight.eero.com/networks/${Math.floor(network.network_id)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {Math.floor(network.network_id)}
                      </a>
                      {network.is_chronic_problem === 1 && (
                        <span className="chronic-badge">
                          CHRONIC
                        </span>
                      )}
                    </td>
                    <td>{network.street_address || 'N/A'}</td>
                    <td>{network.subloc || 'N/A'}</td>
                    <td>{network.customer_name || 'N/A'}</td>
                    <td style={{
                      fontSize: '0.9rem',
                      color: (() => {
                        const result = formatSpeedtest(network.gateway_speed_down, network.download_target)
                        return result.passing === null ? '#666' : result.passing ? '#28a745' : '#dc3545'
                      })(),
                      fontWeight: (() => {
                        const result = formatSpeedtest(network.gateway_speed_down, network.download_target)
                        return result.passing !== null ? '500' : 'normal'
                      })()
                    }}>
                      {formatSpeedtest(network.gateway_speed_down, network.download_target).display}
                    </td>
                    <td style={{
                      fontSize: '0.9rem',
                      color: (() => {
                        const result = formatSpeedtest(network.gateway_speed_up, network.upload_target)
                        return result.passing === null ? '#666' : result.passing ? '#28a745' : '#dc3545'
                      })(),
                      fontWeight: (() => {
                        const result = formatSpeedtest(network.gateway_speed_up, network.upload_target)
                        return result.passing !== null ? '500' : 'normal'
                      })()
                    }}>
                      {formatSpeedtest(network.gateway_speed_up, network.upload_target).display}
                    </td>
                    <td className="outage-count">{network.total_outages}</td>
                    <td className="outage-count">
                      <strong style={network.is_chronic_problem ? {color: '#dc3545'} : {}}>
                        {network.outages_last_24h}
                      </strong>
                    </td>
                    <td>
                      <Link to={`/network/${network.network_id}`} className="btn btn-small">
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No networks found for this property.</p>
        )}
      </div>
    </div>
  )
}

export default PropertyDetail
