import { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis } from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { BarChart2, MapPin, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

import { API_BASE } from '../config';

const STATUS_COLORS = {
  DELIVERED: '#10b981',
  IN_TRANSIT: '#3b82f6',
  CREATED: '#f59e0b',
  FAILED: '#ef4444',
  OUT_FOR_DELIVERY: '#6d28d9',
};

export default function Analytics() {
  const [regional, setRegional] = useState({});
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/analytics/regional`),
      axios.get(`${API_BASE}/analytics/heatmap`)
    ]).then(([regRes, heatRes]) => {
      setRegional(regRes.data);
      setHeatmap(heatRes.data);
    }).finally(() => setLoading(false));
  }, []);

  const regionChartData = Object.entries(regional).map(([region, stats]) => ({
    name: region,
    delivered: stats.delivered,
    in_transit: stats.in_transit,
    failed: stats.failed,
    rate: stats.success_rate
  }));

  const radarData = Object.entries(regional).map(([region, stats]) => ({
    region,
    successRate: stats.success_rate
  }));

  if (loading) return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>Loading analytics...</div>;

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BarChart2 color="var(--accent)" /> Analytics Engine
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>Regional delivery heatmaps, performance breakdowns and fraud signals.</p>
      </div>

      {/* Region Performance Bar Chart */}
      <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Performance by Region</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={regionChartData} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: 'var(--bg-dark)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }} />
            <Bar dataKey="delivered" name="Delivered" fill="#10b981" radius={[4,4,0,0]} />
            <Bar dataKey="in_transit" name="In Transit" fill="#3b82f6" radius={[4,4,0,0]} />
            <Bar dataKey="failed" name="Failed" fill="#ef4444" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Success Rate Radar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="glass-panel">
          <h3 style={{ marginBottom: '1rem' }}>Success Rate by Hub</h3>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="region" tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} />
              <Radar name="Success Rate" dataKey="successRate" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.25} />
              <Tooltip contentStyle={{ background: 'var(--bg-dark)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)' }} formatter={(v) => [`${v}%`, 'Success Rate']} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Regional Summary Table */}
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Region</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Total</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>✓ Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(regional).map(([region, stats]) => (
                <tr key={region} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MapPin size={14} color="var(--text-secondary)" /> {region}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>{stats.total}</td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <span style={{ color: stats.success_rate > 70 ? 'var(--success)' : 'var(--warning)', fontWeight: '700' }}>
                      {stats.success_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Heatmap */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)' }}>
          <h3>Live Shipment Heatmap — India</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
            {heatmap.length} active shipments plotted across Indian hubs
          </p>
        </div>
        {heatmap.length > 0 && (
          <MapContainer center={[20.5937, 78.9629]} zoom={4} scrollWheelZoom={false} style={{ height: '420px', borderRadius: 0 }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; OpenStreetMap'
            />
            {heatmap.map((point, i) => (
              <CircleMarker
                key={i}
                center={[point.lat, point.lng]}
                radius={8}
                pathOptions={{
                  color: STATUS_COLORS[point.status] || '#6d28d9',
                  fillColor: STATUS_COLORS[point.status] || '#6d28d9',
                  fillOpacity: 0.75,
                  weight: 1
                }}
              >
                <Popup>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{point.tracking_code}</div>
                    <div style={{ fontSize: '0.8rem', color: STATUS_COLORS[point.status] }}>{point.status.replace(/_/g, ' ')}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>
    </div>
  );
}
