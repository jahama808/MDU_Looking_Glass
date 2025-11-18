import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, Link } from 'react-router-dom'
import './EquipmentDetail.css'

function Router7x50Detail() {
  const { id } = useParams()
  const [router, setRouter] = useState(null)
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchRouterData()
  }, [id])

  const fetchRouterData = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/7x50/${id}`)
      setRouter(response.data.router)
      setProperties(response.data.properties)
      setError(null)
    } catch (err) {
      setError('Failed to fetch 7x50 router details. Make sure the Flask API server is running.')
      console.error('Error fetching router data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading 7x50 router details...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!router) {
    return <div className="error">7x50 router not found</div>
  }

  return (
    <div className="equipment-detail">
      <div className="breadcrumb">
        <Link to="/equipment">← Back to Equipment</Link>
      </div>

      <div className="equipment-header">
        <h1>{router.router_name}</h1>
        <div className="equipment-type-badge router">7x50 Router</div>
      </div>

      <div className="equipment-summary">
        <div className="summary-item">
          <span className="label">Total Properties:</span>
          <span className="value">{router.total_properties}</span>
        </div>
        <div className="summary-item">
          <span className="label">Total Networks:</span>
          <span className="value">{router.total_networks}</span>
        </div>
      </div>

      <div className="properties-section">
        <h2>Associated Properties ({properties.length})</h2>
        <div className="properties-table">
          <table>
            <thead>
              <tr>
                <th>Property Name</th>
                <th>Networks on this Router</th>
                <th>SAP (LAG)</th>
                <th>Total Outages</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {properties.map((property) => (
                <tr key={property.property_id}>
                  <td>{property.property_name}</td>
                  <td>{property.network_count}</td>
                  <td>{property.saps || 'N/A'}</td>
                  <td className="outage-count">{property.total_outages}</td>
                  <td>
                    <Link
                      to={`/property/${property.property_id}`}
                      className="view-link"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Router7x50Detail
