import { useState, useEffect } from 'react';
import { SESSION_KEYS } from '../constants';

export function useZoom(initialZoom = 1) {
  const [zoom, setZoom] = useState(() => {
    try {
      const saved = sessionStorage.getItem(SESSION_KEYS.ZOOM);
      return saved ? Number(saved) : initialZoom;
    } catch {
      return initialZoom;
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION_KEYS.ZOOM, String(zoom));
    } catch {}
  }, [zoom]);

  useEffect(() => {
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      setZoom((z) => {
        const next = z - e.deltaY * 0.001;
        return Math.min(2, Math.max(0.2, next));
      });
    };
    window.addEventListener('wheel', onWheel, { passive: false });
    return () => window.removeEventListener('wheel', onWheel);
  }, []);

  return zoom;
}
