import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import TrackingView from './pages/TrackingView';
import AuditLogs from './pages/AuditLogs';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import { Package, LogOut, Sun, Moon } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { useThemeStore } from './store/useStore';
import PWAInstallBanner from './components/PWAInstallBanner';
import './index.css';
import 'leaflet/dist/leaflet.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (user.role === 'CUSTOMER') return <Navigate to="/track" />;
  return children;
};

const Header = () => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useThemeStore();

  return (
    <header className="flex-between" style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Package size={32} color="var(--accent)" />
        <h1 className="title-glow" style={{ margin: 0, fontSize: '1.8rem', marginBottom: 0 }}>Orbit Logistics</h1>
      </div>
      <nav style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
        {user && ['ADMIN', 'OPERATOR'].includes(user.role) && (
          <Link to="/" className="nav-link">Dashboard</Link>
        )}
        {user && user.role === 'ADMIN' && (
          <Link to="/audit" className="nav-link">Audit Logs</Link>
        )}
        {user && ['ADMIN', 'OPERATOR'].includes(user.role) && (
          <Link to="/analytics" className="nav-link">Analytics</Link>
        )}
        <Link to="/track" className="nav-link">Track Package</Link>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          style={{ background: 'transparent', border: '1px solid var(--border)', borderRadius: '8px', padding: '6px 10px', cursor: 'pointer', color: 'var(--text-primary)', display: 'flex', alignItems: 'center' }}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{user.email}</span>
            <button onClick={logout} className="btn-primary" style={{ padding: '6px 12px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', boxShadow: 'none' }}>
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <Link to="/login" className="btn-primary" style={{ padding: '8px 16px' }}>Operator Login</Link>
        )}
      </nav>
    </header>
  );
};

function App() {
  const { initTheme } = useThemeStore();

  useEffect(() => {
    initTheme();
  }, []);

  return (
    <AuthProvider>
      <Router>
        <div className="container">
          <Header />
          <main>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/audit" element={<ProtectedRoute><AuditLogs /></ProtectedRoute>} />
              <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
              <Route path="/track" element={<TrackingView />} />
              <Route path="/track/:trackingCode" element={<TrackingView />} />
            </Routes>
          </main>
        </div>
      </Router>
      <PWAInstallBanner />
    </AuthProvider>
  );
}

export default App;
