import { useState, useRef, useCallback, useEffect } from 'react';
import { Pos } from '../store/types';
import { SESSION_KEYS } from '../constants';

export function useNodePositions() {
  const pos = useRef<Record<string, Pos>>({});
  const [tick, setTick] = useState(0);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(SESSION_KEYS.NODE_POSITIONS);
      if (saved) {
        pos.current = JSON.parse(saved);
        setTick((t) => t + 1);
      }
    } catch {}
  }, []);

  const update = useCallback((id: string, x: number, y: number, w: number, h: number) => {
    pos.current[id] = { x, y, w, h };
    try {
      sessionStorage.setItem(SESSION_KEYS.NODE_POSITIONS, JSON.stringify(pos.current));
    } catch {}
    setTick((t) => t + 1);
  }, []);

  return { positions: pos.current, update, tick };
}
