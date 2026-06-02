import { useState, useRef, useCallback } from 'react';
import { Pos } from '../store/types';

export function useNodePositions() {
  const pos = useRef<Record<string, Pos>>({});
  const [tick, setTick] = useState(0);
  const update = useCallback((id: string, x: number, y: number, w: number, h: number) => {
    pos.current[id] = { x, y, w, h };
    setTick(t => t + 1);
  }, []);
  return { positions: pos.current, update, tick };
}
