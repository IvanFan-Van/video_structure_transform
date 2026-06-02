import { useState, useEffect } from 'react';

export function useZoom(initialZoom = 1) {
  const [zoom, setZoom] = useState(initialZoom);

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
