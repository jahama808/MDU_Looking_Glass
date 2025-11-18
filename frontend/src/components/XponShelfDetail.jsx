import { useState, useEffect } from 'react'
import axios from 'axios'
import { useParams, Link } from 'react-router-dom'
import './EquipmentDetail.css'

function XponShelfDetail() {
  const { id } = useParams()
  const [shelf, setShelf] = useState(null)
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchShelfData()
  }, [id])

  const fetchShelfData = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/xpon-shelf/${id}`)
      setShelf(response.data.shelf)
      setProperties(response.data.properties)
      setError(null)
    } catch (err) {
      setError('Failed to fetch xPON shelf details. Make sure the Flask API server is running.')
      console.error('Error fetching shelf data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading xPON shelf details...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!shelf) {
    return <div className="error">xPON shelf not found</div>
  }

  return (
    <div className="equipment-detail">
      <div className="breadcrumb">
        <Link to="/equipment">← Back to Equipment</Link>
      </div>

      <div className="equipment-header">
        <h1>{shelf.shelf_name}</h1>
        <div className="equipment-type-badge">xPON Shelf</div>
      </div>

      <div className="equipment-summary">
        <div className="summary-item">
          <span className="label">Total Properties:</span>
          <span className="value">{shelf.total_properties}</span>
        </div>
        <div className="summary-item">
          <span className="label">Total Networks:</span>
          <span className="value">{shelf.total_networks}</span>
        </div>
      </div>

      <div className="properties-section">
        <h2>Associated Properties ({properties.length})</h2>
        <div className="properties-table">
          <table>
            <thead>
              <tr>
                <th>Property Name</th>
                <th>Networks on this Shelf</th>
                <th>Slots</th>
                <th>PONs</th>
                <th>Total Outages</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {properties.map((property) => (
                <tr key={property.property_id}>
                  <td>{property.property_name}</td>
                  <td>{property.network_count}</td>
                  <td>{property.slots || 'N/A'}</td>
                  <td>{property.pons || 'N/A'}</td>
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

export default XponShelfDetail
