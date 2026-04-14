import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { MapPin, Filter, Package, CheckCircle, Clock, AlertTriangle, List, Map, RefreshCw, Radio } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useShipmentStore } from '../store/useStore';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';
import MapComponent from '../components/MapComponent';

import { API_BASE } from '../config';
const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#6d28d9', '#ef4444'];

const KPI_COLORS = {
  delivered: '#10b981',
  pending: '#f59e0b',
  in_transit: '#3b82f6',
  failed: '#ef4444',
};

export default function Dashboard() {
  const { user } = useAuth();
  const { shipments, kpis, loading, lastUpdated, fetchShipments, fetchKpis } = useShipmentStore();
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'
  const [wsStatus, setWsStatus] = useState('connecting');

  useWebSocket();

  useEffect(() => {
    fetchShipments();
    fetchKpis();

    // Simulate WS connection status from the hook state
    const t = setTimeout(() => setWsStatus('connected'), 1500);
    return () => clearTimeout(t);
  }, []);

  const filteredShipments = statusFilter === 'ALL'
    ? shipments
    : shipments.filter(s => s.current_status === statusFilter);

  const pieData = kpis ? [
    { name: 'Delivered', value: kpis.delivered },
    { name: 'Pending', value: kpis.pending },
    { name: 'In Transit', value: kpis.in_transit },
    { name: 'Failed', value: kpis.failed },
  ].filter(d => d.value > 0) : [];

  const barData = kpis ? [
    { name: 'Delivered', count: kpis.delivered, color: KPI_COLORS.delivered },
    { name: 'In Transit', count: kpis.in_transit, color: KPI_COLORS.in_transit },
    { name: 'Pending', count: kpis.pending, color: KPI_COLORS.pending },
    { name: 'Failed', count: kpis.failed, color: KPI_COLORS.failed },
  ] : [];

  if (loading && shipments.length === 0) return <div style={{ textAlign: 'center', padding: '40px' }}>Loading dashboard...</div>;

  return (
    <div>
      <div className="flex-between" style={{ marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '4px' }}>Welcome back, {user?.full_name}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {lastUpdated && `Last refreshed: ${lastUpdated.toLocaleTimeString()}`}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className={`ws-indicator ${wsStatus === 'connected' ? 'ws-connected' : 'ws-disconnected'}`}>
            <Radio size={10} /> {wsStatus === 'connected' ? 'Live' : 'Connecting...'}
          </span>
          <button onClick={() => { fetchShipments(); fetchKpis(); }} style={{ background: 'transparent', border: '1px solid var(--border)', borderRadius: '8px', padding: '8px 12px', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '2rem' }}>
          {[
            { label: 'Total', value: kpis.total, icon: <Package size={22} />, color: '#6d28d9' },
            { label: 'Delivered', value: kpis.delivered, icon: <CheckCircle size={22} />, color: '#10b981' },
            { label: 'In Transit', value: kpis.in_transit, icon: <MapPin size={22} />, color: '#3b82f6' },
            { label: 'Pending', value: kpis.pending, icon: <Clock size={22} />, color: '#f59e0b' },
            { label: 'Avg Delivery', value: `${kpis.avg_delivery_time_hours}h`, icon: <Clock size={22} />, color: '#6d28d9' },
          ].map(kpi => (
            <div key={kpi.label} className="glass-panel" style={{ padding: '18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ padding: '10px', background: `${kpi.color}20`, borderRadius: '10px', color: kpi.color }}>{kpi.icon}</div>
              <div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{kpi.label}</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 'bold' }}>{kpi.value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Charts Row */}
      {kpis && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', marginBottom: '2rem' }}>
          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Shipment Distribution</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={Object.values(KPI_COLORS)[index]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-dark)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Status Breakdown</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={barData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-dark)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Shipment List / Map */}
      <div className="flex-between" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.3rem', fontWeight: '600' }}>Active Shipments ({filteredShipments.length})</h3>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <Filter size={18} color="var(--text-secondary)" />
          <select className="input-field" style={{ width: 'auto' }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="ALL">All Statuses</option>
            <option value="CREATED">Created</option>
            <option value="IN_TRANSIT">In Transit</option>
            <option value="OUT_FOR_DELIVERY">Out for Delivery</option>
            <option value="DELIVERED">Delivered</option>
            <option value="FAILED">Failed</option>
          </select>
          <div style={{ display: 'flex', border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
            <button onClick={() => setViewMode('list')} style={{ padding: '8px 12px', background: viewMode === 'list' ? 'var(--accent)' : 'transparent', border: 'none', cursor: 'pointer', color: 'white', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem' }}>
              <List size={16} /> List
            </button>
            <button onClick={() => setViewMode('map')} style={{ padding: '8px 12px', background: viewMode === 'map' ? 'var(--accent)' : 'transparent', border: 'none', cursor: 'pointer', color: 'white', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem' }}>
              <Map size={16} /> Map
            </button>
          </div>
        </div>
      </div>

      {viewMode === 'map' ? (
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <MapComponent
            events={filteredShipments.flatMap(s => s.events || [])}
            current_lat={filteredShipments[0]?.current_lat}
            current_lng={filteredShipments[0]?.current_lng}
          />
        </div>
      ) : (
        <div className="dashboard-grid">
          {filteredShipments.map(shipment => (
            <div key={shipment.id} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div className="flex-between">
                <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{shipment.tracking_code}</span>
                <span className={`status-badge status-${shipment.current_status}`}>{shipment.current_status.replace(/_/g, ' ')}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', padding: '12px', background: 'rgba(0,0,0,0.15)', borderRadius: '10px' }}>
                <div><div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '2px' }}>Weight</div><div style={{ fontWeight: '600' }}>{shipment.weight} kg</div></div>
                <div><div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '2px' }}>Type</div><div style={{ fontWeight: '600' }}>{shipment.type}</div></div>
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <MapPin size={14} color="var(--text-secondary)" /><span style={{ fontSize: '0.9rem' }}>{shipment.origin}</span>
                </div>
                <div style={{ paddingLeft: '7px', height: '14px', borderLeft: '2px dashed var(--border)', marginLeft: '6px' }}></div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MapPin size={14} color="var(--accent)" /><span style={{ fontSize: '0.9rem' }}>{shipment.destination}</span>
                </div>
              </div>

              <div style={{ marginTop: 'auto', paddingTop: '14px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={async () => {
                    try {
                      await axios.post(`${API_BASE}/shipments/${shipment.tracking_code}/pulse`);
                      fetchShipments();
                    } catch(e) { console.error("Sim error", e); }
                  }}
                  style={{ background: 'transparent', border: '1px solid var(--accent)', borderRadius: '6px', padding: '5px 10px', cursor: 'pointer', color: 'var(--accent)', fontSize: '0.78rem', fontWeight: '600' }}
                >
                  Pulse GPS
                </button>
                <Link to={`/track/${shipment.tracking_code}`} className="btn-primary" style={{ padding: '7px 14px', fontSize: '0.85rem' }}>
                  Track Journey
                </Link>
              </div>
            </div>
          ))}
          {filteredShipments.length === 0 && (
            <p style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--text-secondary)', padding: '40px' }}>
              No shipments found for the selected status.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
