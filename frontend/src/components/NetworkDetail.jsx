import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './NetworkDetail.css'

function NetworkDetail() {
  const { id } = useParams()
  const [network, setNetwork] = useState(null)
  const [hourlyData, setHourlyData] = useState([])
  const [ongoingOutages, setOngoingOutages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchNetworkData()
  }, [id])

  const fetchNetworkData = async () => {
    try {
      setLoading(true)
      const [networkRes, hourlyRes] = await Promise.all([
        axios.get(`/api/network/${id}`),
        axios.get(`/api/network/${id}/hourly`)
      ])

      setNetwork(networkRes.data)

      // Try to fetch ongoing outages (optional)
      try {
        const ongoingRes = await axios.get(`/api/network/${id}/ongoing-outages`)
        setOngoingOutages(ongoingRes.data)
      } catch (err) {
        console.log('Ongoing outages feature not available')
        setOngoingOutages([])
      }

      // Format hourly data for chart
      const formattedHourly = hourlyRes.data.map(item => ({
        time: new Date(item.outage_hour).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit'
        }),
        outages: item.outage_count
      }))
      setHourlyData(formattedHourly)

      setError(null)
    } catch (err) {
      setError('Failed to fetch network details. Make sure the Flask API server is running.')
      console.error('Error fetching network data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading network details...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!network) {
    return <div className="error">Network not found</div>
  }

  return (
    <div className="network-detail">
      <div className="breadcrumb">
        <Link to="/properties">← Back to Properties</Link>
      </div>

      <div className="network-header">
        <h1>Network Details</h1>
        <div className="network-info">
          <div className="info-row">
            <span className="label">Network ID:</span>
            <span className="value">
              <a
                href={`https://insight.eero.com/networks/${network.network_id}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{color: '#667eea', textDecoration: 'none', fontWeight: '600'}}
              >
                {network.network_id}
              </a>
            </span>
          </div>
          <div className="info-row">
            <span className="label">Property:</span>
            <span className="value">
              <Link
                to={`/property/${network.property_id}`}
                style={{color: '#667eea', textDecoration: 'none', fontWeight: '600'}}
              >
                {network.property_name}
              </Link>
            </span>
          </div>
          <div className="info-row">
            <span className="label">Address:</span>
            <span className="value">{network.street_address || 'N/A'}</span>
          </div>
          <div className="info-row">
            <span className="label">Unit:</span>
            <span className="value">{network.subloc || 'N/A'}</span>
          </div>
          <div className="info-row">
            <span className="label">Customer:</span>
            <span className="value">{network.customer_name || 'N/A'}</span>
          </div>
          <div className="info-row">
            <span className="label">Total Outages:</span>
            <span className="value outage-count">{network.total_outages}</span>
          </div>
        </div>
      </div>

      {(network.xpon_shelf || network.router_7x50_info) && (
        <div className="equipment-section">
          <h2>Network Equipment</h2>
          <div className="equipment-grid">
            {network.xpon_shelf && (
              <div className="equipment-card">
                <h3>xPON OLT Shelf</h3>
                <div className="equipment-list">
                  <div className="equipment-item">
                    <div className="equipment-name">{network.xpon_shelf.shelf_name}</div>
                    {network.equip_name && (
                      <div className="equipment-details">
                        <span className="olt-id">OLT ID: {network.equip_name}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            {network.router_7x50_info && (
              <div className="equipment-card">
                <h3>7x50 Router</h3>
                <div className="equipment-list">
                  <div className="equipment-item">
                    <div className="equipment-name">{network.router_7x50_info.router_name}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {ongoingOutages.length > 0 && (
        <div className="ongoing-outages-section">
          <h2>🔴 Network Currently Down</h2>
          <div className="ongoing-outages-alert">
            <strong>Active Outage:</strong> This network is currently experiencing an outage.
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
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {hourlyData.length > 0 && (
        <div className="chart-section">
          <h2>Hourly Outage Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="outages"
                stroke="#82ca9d"
                strokeWidth={2}
                name="Outages"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

export default NetworkDetail
