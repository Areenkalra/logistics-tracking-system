import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Search, MapPin, AlertCircle } from 'lucide-react';
import MapComponent from '../components/MapComponent';

import { API_BASE } from '../config';

export default function TrackingView() {
  const { trackingCode } = useParams();
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState(trackingCode || '');
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (trackingCode) {
      fetchTracking(trackingCode);
    }
  }, [trackingCode]);

  const fetchTracking = async (query) => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${API_BASE}/track/search?query=${query}`);
      setShipments(response.data);
    } catch (err) {
      setError("We couldn't find a shipment with that tracking code, phone, or email. Please double-check and try again.");
      setShipments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    navigate(`/track/${searchInput.trim()}`);
  };

  return (
    <div>
      <div className="glass-panel" style={{ marginBottom: '2rem', padding: '30px' }}>
        <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Track Your Package</h2>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', maxWidth: '600px', margin: '0 auto' }}>
          <input 
            type="text" 
            className="input-field" 
            placeholder="Enter Tracking Code, Phone, or Email Address"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            <Search size={20} />
            Track
          </button>
        </form>
        <div style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Try sample codes: <span style={{ fontFamily: 'monospace', cursor: 'pointer', color: 'var(--accent)', textDecoration: 'underline' }} onClick={() => setSearchInput('TRK-SAMPLE01')}>TRK-SAMPLE01</span>, <span style={{ fontFamily: 'monospace', cursor: 'pointer', color: 'var(--accent)', textDecoration: 'underline' }} onClick={() => setSearchInput('TRK-SAMPLE02')}>TRK-SAMPLE02</span>
        </div>
        {error && (
          <div style={{ marginTop: '1rem', color: 'var(--warning)', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <AlertCircle size={18} />
            {error}
          </div>
        )}
      </div>

      {loading && <p style={{ textAlign: 'center' }}>Searching...</p>}

      {!loading && shipments.length > 0 && shipments.map((shipment) => (
        <div key={shipment.id} style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '24px', marginBottom: '3rem' }}>
          
          <div className="glass-panel">
            <div className="flex-between" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0 }}>Details</h3>
              <span className={`status-badge status-${shipment.current_status}`}>
                {shipment.current_status.replace(/_/g, ' ')}
              </span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '1.5rem' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Tracking Code</div>
              <div style={{ fontFamily: 'monospace', fontSize: '1.2rem', letterSpacing: '2px' }}>{shipment.tracking_code}</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', marginBottom: '1.5rem' }}>
               <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Weight</div>
                  <div style={{ fontWeight: '500' }}>{shipment.weight} kg</div>
               </div>
               <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Type</div>
                  <div style={{ fontWeight: '500' }}>{shipment.type}</div>
               </div>
            </div>

            {shipment.estimated_delivery_date && (
                <div className="glass-panel" style={{ background: 'rgba(var(--accent-rgb), 0.1)', border: '1px solid var(--accent)', marginBottom: '1.5rem', padding: '15px' }}>
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent)', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: '4px' }}>Expected Delivery By</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: '800' }}>
                        {new Date(shipment.estimated_delivery_date).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
                    </div>
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '8px' }}>Journey Log</div>
                <div className="timeline-container">
                  {shipment.events.map((event, idx) => {
                    const isLatest = idx === 0;
                    return (
                      <div key={event.id} className="timeline-item">
                        <div className="timeline-dot" style={{ 
                          background: isLatest ? 'var(--accent)' : 'var(--text-secondary)', 
                          boxShadow: isLatest ? '0 0 10px var(--accent-glow)' : 'none',
                          border: isLatest ? '2px solid white' : 'none',
                          left: isLatest ? '-33px' : '-31px',
                          width: isLatest ? '14px' : '12px',
                          height: isLatest ? '14px' : '12px'
                        }}></div>
                        <div className="flex-between">
                          <div className="timeline-title" style={{ color: isLatest ? 'white' : 'var(--text-secondary)' }}>{event.status.replace(/_/g, ' ')}</div>
                          <div className="timeline-date">{new Date(event.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</div>
                        </div>
                        <div className="timeline-desc" style={{ color: isLatest ? '#ddd' : 'var(--text-secondary)' }}>{event.description}</div>
                        <div style={{ fontSize: '0.85rem', color: isLatest ? 'var(--info)' : 'var(--text-secondary)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <MapPin size={14} /> {event.location_name}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          <div>
             <MapComponent events={shipment.events} current_lat={shipment.current_lat} current_lng={shipment.current_lng} />
          </div>

        </div>
      ))}
    </div>
  );
}
