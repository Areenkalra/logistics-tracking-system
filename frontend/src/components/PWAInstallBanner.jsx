import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';

export default function PWAInstallBanner() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowBanner(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShowBanner(false);
      setDeferredPrompt(null);
    }
  };

  if (!showBanner) return null;

  return (
    <div className="pwa-install-banner" onClick={handleInstall}>
      <Download size={18} />
      Install Orbit Logistics as App
      <button onClick={(e) => { e.stopPropagation(); setShowBanner(false); }} style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', marginLeft: '8px', opacity: 0.7 }}>✕</button>
    </div>
  );
}
