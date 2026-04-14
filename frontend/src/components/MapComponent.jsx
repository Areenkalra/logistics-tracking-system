import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';

// Fix Leaflet icons issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom highlighted marker for current location (Pulsing blue)
const liveIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [30, 46],
  iconAnchor: [15, 46],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function MapComponent({ events, current_lat, current_lng }) {
  if (!events || events.length === 0) return <div className="glass-panel" style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>No location data available yet.</div>;

  // Filter events that have lat/lng
  const validEvents = events.filter(e => e.lat !== 0 && e.lng !== 0);
  
  if (validEvents.length === 0) return <div className="glass-panel" style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Awaiting location coordinates.</div>;

  // Most recent event is first (assuming sorted descending by timestamp)
  const currentLoc = validEvents[0];
  const center = [currentLoc.lat, currentLoc.lng];

  // Route positions
  const positions = validEvents.map(e => [e.lat, e.lng]);

  return (
    <MapContainer center={center} zoom={5} scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      <Polyline positions={positions} color="var(--accent)" weight={4} opacity={0.6} dashArray="8, 8" />
      
      {validEvents.map((event, idx) => (
        <Marker 
          key={event.id} 
          position={[event.lat, event.lng]}
          icon={new L.Icon.Default()}
        >
          <Popup>
            <strong style={{ color: 'var(--accent)' }}>{event.location_name}</strong><br/>
            {event.status.replace(/_/g, ' ')}<br/>
            <small style={{ color: 'var(--text-secondary)' }}>{new Date(event.timestamp).toLocaleString()}</small>
          </Popup>
        </Marker>
      ))}

      {current_lat && current_lng && (
        <Marker 
          position={[current_lat, current_lng]}
          icon={liveIcon}
        >
          <Popup>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 'bold', color: 'var(--info)' }}>LIVE LOCATION</div>
                <div style={{ fontSize: '0.8rem' }}>Coordinates: {current_lat.toFixed(4)}, {current_lng.toFixed(4)}</div>
            </div>
          </Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
