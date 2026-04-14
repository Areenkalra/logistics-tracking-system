import { useEffect, useRef, useCallback } from 'react';
import { useShipmentStore } from '../store/useStore';
import { WS_URL } from '../config';

export function useWebSocket() {
  const ws = useRef(null);
  const { updateShipmentFromEvent, fetchShipments, fetchKpis } = useShipmentStore();
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log("[WS] Connected to real-time updates");
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("[WS] Event received:", data);
          if (data.type === 'STATUS_UPDATE') {
            updateShipmentFromEvent(data.tracking_code, data.status, data.location);
            fetchKpis(); // Refresh KPIs
          } else if (data.type === 'SHIPMENT_CREATED') {
            fetchShipments(); // Full refresh on new shipment
          }
        } catch (e) {
          console.error("[WS] Message parse error", e);
        }
      };

      ws.current.onclose = (e) => {
        console.log("[WS] Disconnected. Reconnecting in 3s...");
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.current.onerror = (e) => {
        console.warn("[WS] Error occurred, closing...");
        ws.current?.close();
      };
    } catch (e) {
      console.warn("[WS] Failed to connect:", e);
    }
  }, [updateShipmentFromEvent, fetchShipments, fetchKpis]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);
}
