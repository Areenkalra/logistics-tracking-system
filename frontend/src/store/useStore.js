import { create } from 'zustand';
import axios from 'axios';
import { API_BASE } from '../config';

export const useShipmentStore = create((set, get) => ({
  shipments: [],
  kpis: null,
  loading: false,
  lastUpdated: null,

  fetchShipments: async () => {
    set({ loading: true });
    try {
      const res = await axios.get(`${API_BASE}/shipments?per_page=50`);
      set({ shipments: res.data.results || res.data, lastUpdated: new Date() });
    } catch (e) {
      console.error("Failed to fetch shipments", e);
    } finally {
      set({ loading: false });
    }
  },

  fetchKpis: async () => {
    try {
      const res = await axios.get(`${API_BASE}/dashboard/kpi`);
      set({ kpis: res.data });
    } catch (e) {
      console.error("Failed to fetch KPIs", e);
    }
  },

  updateShipmentFromEvent: (trackingCode, newStatus, location) => {
    set(state => ({
      shipments: state.shipments.map(s =>
        s.tracking_code === trackingCode
          ? { ...s, current_status: newStatus }
          : s
      )
    }));
  }
}));

export const useThemeStore = create((set) => ({
  isDark: localStorage.getItem('theme') !== 'light',
  
  toggleTheme: () => set(state => {
    const isDark = !state.isDark;
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
    return { isDark };
  }),

  initTheme: () => {
    const isLight = localStorage.getItem('theme') === 'light';
    if (isLight) {
      document.documentElement.setAttribute('data-theme', 'light');
      set({ isDark: false });
    }
  }
}));
