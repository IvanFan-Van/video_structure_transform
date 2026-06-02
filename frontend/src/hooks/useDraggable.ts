import { useState, useRef, useCallback, useEffect } from 'react';

export function useDraggable(ix: number, iy: number, id: string, onPos: (id: string, x: number, y: number, w: number, h: number) => void) {
  const [p, setP] = useState({ x: ix, y: iy });
  const drag = useRef(false);
  const off = useRef({ x: 0, y: 0 });
  const ref = useRef<HTMLDivElement>(null);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes((e.target as HTMLElement).tagName)) return;
    drag.current = true;
    off.current = { x: e.clientX - p.x, y: e.clientY - p.y };
    e.preventDefault();
  }, [p]);

  useEffect(() => {
    const mv = (e: MouseEvent) => { if (drag.current) setP({ x: e.clientX - off.current.x, y: e.clientY - off.current.y }); };
    const up = () => { drag.current = false; };
    window.addEventListener('mousemove', mv);
    window.addEventListener('mouseup', up);
    return () => { window.removeEventListener('mousemove', mv); window.removeEventListener('mouseup', up); };
  }, []);

  useEffect(() => {
    if (ref.current) {
      const r = ref.current.getBoundingClientRect();
      onPos(id, p.x, p.y, r.width, r.height);
    }
  }, [p, id, onPos]);

  return { p, onMouseDown, ref };
}
