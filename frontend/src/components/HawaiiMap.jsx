import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Polygon, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './HawaiiMap.css'

// Component to update map view when island is selected
function MapViewController({ selectedIsland, islandCoordinates }) {
  const map = useMap()

  useEffect(() => {
    if (selectedIsland && islandCoordinates[selectedIsland]) {
      // Get the bounds of the selected island
      const coords = islandCoordinates[selectedIsland]
      const bounds = coords.map(coord => [coord[0], coord[1]])
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 })
    } else {
      // Show all islands
      map.setView([20.5, -157], 7)
    }
  }, [selectedIsland, map, islandCoordinates])

  return null
}

function HawaiiMap({ selectedIsland, onIslandSelect }) {
  // Approximate polygon coordinates for each Hawaiian island
  // Format: [latitude, longitude]
  const islandCoordinates = {
    'Kauai': [
      [22.21, -159.65],
      [22.21, -159.30],
      [21.87, -159.30],
      [21.87, -159.65]
    ],
    'Oahu': [
      [21.71, -158.28],
      [21.71, -157.65],
      [21.25, -157.65],
      [21.25, -158.28]
    ],
    'Molokai': [
      [21.20, -157.30],
      [21.20, -156.70],
      [21.05, -156.70],
      [21.05, -157.30]
    ],
    'Lanai': [
      [20.90, -157.10],
      [20.90, -156.85],
      [20.72, -156.85],
      [20.72, -157.10]
    ],
    'Maui': [
      [21.05, -156.70],
      [21.05, -155.95],
      [20.55, -155.95],
      [20.55, -156.70]
    ],
    'Hawaii': [
      [20.27, -156.08],
      [20.27, -154.80],
      [18.91, -154.80],
      [18.91, -156.08]
    ]
  }

  const handleIslandClick = (islandName) => {
    // If clicking the already selected island, deselect it (show all)
    if (selectedIsland === islandName) {
      onIslandSelect(null)
    } else {
      onIslandSelect(islandName)
    }
  }

  const getIslandStyle = (islandName) => {
    const isSelected = selectedIsland === islandName
    const isDimmed = selectedIsland && selectedIsland !== islandName

    return {
      fillColor: isSelected ? '#2ecc71' : '#27ae60',
      fillOpacity: isDimmed ? 0.3 : 0.5,
      color: isSelected ? '#fff' : '#1e7d46',
      weight: isSelected ? 3 : 2,
      className: 'island-polygon'
    }
  }

  return (
    <div className="hawaii-map-container">
      <div className="map-header">
        <h3>Filter by Island</h3>
        {selectedIsland && (
          <button
            className="reset-filter-btn"
            onClick={() => onIslandSelect(null)}
            title="Show all islands"
          >
            ✕ Clear Filter
          </button>
        )}
      </div>

      <MapContainer
        center={[20.5, -157]}
        zoom={7}
        className="hawaii-map"
        scrollWheelZoom={true}
        zoomControl={true}
      >
        {/* Satellite imagery from ESRI */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        {/* Optional: Add labels overlay */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          maxZoom={18}
        />

        {/* Island polygons */}
        {Object.entries(islandCoordinates).map(([name, coordinates]) => (
          <Polygon
            key={name}
            positions={coordinates}
            pathOptions={getIslandStyle(name)}
            eventHandlers={{
              click: () => handleIslandClick(name)
            }}
          >
            <Tooltip direction="center" permanent={true} className="island-label">
              {name}
            </Tooltip>
          </Polygon>
        ))}

        {/* View controller to handle zoom/pan on selection */}
        <MapViewController
          selectedIsland={selectedIsland}
          islandCoordinates={islandCoordinates}
        />
      </MapContainer>

      <div className="map-legend">
        {selectedIsland ? (
          <div className="filter-active">
            Showing properties on <strong>{selectedIsland}</strong>
          </div>
        ) : (
          <div className="filter-inactive">
            Click an island to filter properties
          </div>
        )}
      </div>
    </div>
  )
}

export default HawaiiMap
