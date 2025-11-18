# Property Outage Web Application

A full-stack web application built with React and Flask to visualize and monitor property network outages.

## Architecture

- **Frontend**: React with Vite, Recharts for data visualization, React Router for navigation
- **Backend**: Flask REST API with CORS support
- **Database**: SQLite (output/outages.db)

## Features

- **Dashboard**: Overview statistics of all properties and outages
- **Property List**: Searchable list of all properties with outage counts
- **Property Details**: Detailed view with hourly outage trends and network breakdown
- **Network Details**: Individual network information with hourly outage patterns
- **Interactive Charts**: Visual representation of outage patterns over time

## Quick Start

### Prerequisites

- Python 3.x with virtual environment activated
- Node.js v18+ and npm
- Database file at `output/outages.db` (create using `process_property_outages_db.py`)

### Installation

The frontend and backend dependencies should already be installed. If not:

```bash
# Backend dependencies (in virtual environment)
source venv/bin/activate
pip install flask flask-cors

# Frontend dependencies
cd frontend
npm install
```

### Running the Application

You need to run both the backend and frontend servers. Open **two separate terminals**:

#### Terminal 1 - Backend (Flask API)

```bash
# From project root directory
./start_backend.sh

# Or manually:
source venv/bin/activate
python api_server.py
```

The Flask API will start on: **http://localhost:5000**

#### Terminal 2 - Frontend (React)

```bash
# From project root directory
./start_frontend.sh

# Or manually:
cd frontend
npm run dev
```

The React app will start on: **http://localhost:5173**

### Accessing the Application

Open your web browser and navigate to: **http://localhost:5173**

## API Endpoints

The Flask backend provides these REST API endpoints:

- `GET /` - API documentation
- `GET /api/properties` - Get all properties with outages
- `GET /api/property/<id>` - Get property details
- `GET /api/property/<id>/hourly` - Get hourly outage data for property
- `GET /api/property/<id>/networks` - Get networks for property
- `GET /api/network/<id>` - Get network details
- `GET /api/network/<id>/hourly` - Get hourly outage data for network
- `GET /api/stats` - Get overall statistics
- `GET /api/search?q=<query>` - Search properties by name

## Project Structure

```
theNewOutageLookingGlass/
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── PropertyList.jsx
│   │   │   ├── PropertyDetail.jsx
│   │   │   └── NetworkDetail.jsx
│   │   ├── App.jsx          # Main app component with routing
│   │   └── main.jsx         # Entry point
│   ├── package.json
│   └── vite.config.js       # Vite config with API proxy
│
├── api_server.py            # Flask backend server
├── output/outages.db        # SQLite database
├── start_backend.sh         # Backend startup script
└── start_frontend.sh        # Frontend startup script
```

## Development

### Frontend Development

The React app uses Vite for fast hot-module replacement (HMR). Any changes to React components will automatically update in the browser.

API calls from the frontend are automatically proxied to the Flask backend (configured in `vite.config.js`).

### Backend Development

The Flask app runs in debug mode, so changes to Python files will automatically reload the server.

### Building for Production

To build the frontend for production:

```bash
cd frontend
npm run build
```

The production build will be in the `frontend/dist` directory.

## Troubleshooting

### Flask server won't start

- Make sure you're in the virtual environment: `source venv/bin/activate`
- Check that Flask is installed: `pip list | grep Flask`
- Verify the database exists: `ls -lh output/outages.db`

### React app shows "Failed to fetch" errors

- Make sure the Flask backend is running on port 5000
- Check browser console for CORS errors
- Verify the API proxy is configured in `vite.config.js`

### No data is showing

- Ensure the database file exists and has data
- Run the data processing script first: `python process_property_outages_db.py --outages-file wan_connectivity.csv --discovery-file eero_discovery.csv --database output/outages.db`

### Port already in use

If port 5000 or 5173 is already in use:

- Flask: Set a different port in `api_server.py`: `app.run(port=5001)`
- React: Vite will automatically try the next available port

## Technologies Used

### Frontend

- **React 18**: UI library
- **React Router 7**: Client-side routing
- **Axios**: HTTP client for API calls
- **Recharts**: Charting library for data visualization
- **Vite**: Build tool and dev server

### Backend

- **Flask**: Python web framework
- **Flask-CORS**: Cross-Origin Resource Sharing support
- **SQLite3**: Database

## License

This project is part of the Property Outage Monitoring System.
