import { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Clock, User, Package, History } from 'lucide-react';

import { API_BASE } from '../config';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/audit`);
      setLogs(res.data);
    } catch (error) {
      console.error("Error fetching audit logs:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '40px' }}>Loading audit logs...</div>;

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield color="var(--accent)" /> Audit System Logs
        </h2>
        <p style={{ color: 'var(--text-secondary)' }}>Traceability for all shipment status modifications and creations.</p>
      </div>

      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left' }}>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: '600' }}>Timestamp</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: '600' }}>Operator ID</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: '600' }}>Action</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: '600' }}>Shipment</th>
              <th style={{ padding: '16px', color: 'var(--text-secondary)', fontWeight: '600' }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '16px', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={14} color="var(--text-secondary)" />
                    {new Date(log.timestamp).toLocaleString()}
                  </div>
                </td>
                <td style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <User size={14} color="var(--text-secondary)" />
                    User #{log.user_id}
                  </div>
                </td>
                <td style={{ padding: '16px' }}>
                  <span style={{ 
                    padding: '4px 8px', 
                    borderRadius: '4px', 
                    background: log.action === 'STATUS_UPDATE' ? 'rgba(var(--accent-rgb), 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    color: log.action === 'STATUS_UPDATE' ? 'var(--accent)' : 'var(--success)',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {log.action}
                  </span>
                </td>
                <td style={{ padding: '16px', fontFamily: 'monospace' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Package size={14} color="var(--text-secondary)" />
                    {log.target_shipment}
                  </div>
                </td>
                <td style={{ padding: '16px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {log.details}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No audit records found.
          </div>
        )}
      </div>
    </div>
  );
}
