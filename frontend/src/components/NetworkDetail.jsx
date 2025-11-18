import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './NetworkDetail.css'

function NetworkDetail() {
  const { id } = useParams()
  const [network, setNetwork] = useState(null)
  const [hourlyData, setHourlyData] = useState([])
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
            <span className="value">{network.property_name}</span>
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
