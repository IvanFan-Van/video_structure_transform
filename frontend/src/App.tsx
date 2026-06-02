import { useState, useEffect } from 'react';
import { Wires } from './components/ui/Wires';
import { useNodePositions } from './hooks/useNodePositions';
import { useAppStore } from './store/useAppStore';
import { WIRES } from './constants';
import { DatasetNode } from './components/nodes/DatasetNode';
import { TokenizerNode } from './components/nodes/TokenizerNode';
import { ArchitectureNode } from './components/nodes/ArchitectureNode';
import { TrainingNode } from './components/nodes/TrainingNode';
import { MetricsNode } from './components/nodes/MetricsNode';
import { GenerateNode } from './components/nodes/GenerateNode';

function App() {
  const { positions, update: updatePos, tick: posTick } = useNodePositions();
  const initWorker = useAppStore((s) => s.initWorker);
  const destroyWorker = useAppStore((s) => s.destroyWorker);
  const modelReady = useAppStore((s) => s.modelReady);
  const saveRunHistory = useAppStore((s) => s.saveRunHistory);

  useEffect(() => {
    initWorker();
    return () => destroyWorker();
  }, []);

  useEffect(() => {
    if (modelReady) saveRunHistory();
  }, [modelReady, saveRunHistory]);

  const [offset, setOffset] = useState(60);
  useEffect(() => {
    const calcOffset = () => {
      const totalWidth = 1140;
      const ox = Math.max(60, Math.floor((window.innerWidth - totalWidth) / 2));
      setOffset(ox);
    };
    calcOffset();
    window.addEventListener('resize', calcOffset);
    return () => window.removeEventListener('resize', calcOffset);
  }, []);

  return (
    <div style={{
      width: '100vw', height: '100vh', overflow: 'auto', position: 'relative',
      fontFamily: "'JetBrains Mono', monospace", background: '#fafafa',
      backgroundImage: 'radial-gradient(circle, #e0e0e0 0.8px, transparent 0.8px)', backgroundSize: '20px 20px',
    }}>
      <div style={{ position: 'fixed', top: 16, left: 20, zIndex: 100, fontSize: '10px', fontWeight: 700, letterSpacing: '3px', color: '#ccc' }}>TRAIN MY OWN GPT</div>
      <a href="https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95" target="_blank" rel="noopener noreferrer"
        style={{ position: 'fixed', top: 16, right: 20, zIndex: 100, fontSize: '9px', letterSpacing: '1px', color: '#ccc', textDecoration: 'none', cursor: 'pointer' }}
        onMouseEnter={(e) => e.currentTarget.style.color = '#999'}
        onMouseLeave={(e) => e.currentTarget.style.color = '#ccc'}
      >based on karpathy&apos;s microgpt · runs in your browser</a>

      <Wires positions={positions} wires={WIRES} tick={posTick} />

      <DatasetNode x={offset} y={80} onPosChange={updatePos} />
      <TokenizerNode x={offset} y={380} onPosChange={updatePos} />

      <ArchitectureNode x={offset + 310} y={80} onPosChange={updatePos} />
      <TrainingNode x={offset + 310} y={440} onPosChange={updatePos} />

      <MetricsNode x={offset + 640} y={80} onPosChange={updatePos} />
      <GenerateNode x={offset + 640} y={440} onPosChange={updatePos} />

      <div style={{ position: 'fixed', bottom: 16, left: 20, zIndex: 100, fontSize: '8px', color: '#ccc', letterSpacing: '0.5px' }}>
        100% in-browser · no data leaves your device
      </div>

      <div style={{ position: 'fixed', bottom: 16, right: 20, zIndex: 100, display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span style={{ fontSize: '8px', color: '#ddd', letterSpacing: '0.5px' }}>built by jay</span>
        <a href="https://github.com/jayyvk/trainmyowngpt" target="_blank" rel="noopener noreferrer" style={{ color: '#ccc', transition: 'color 0.2s' }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#666'} onMouseLeave={(e) => e.currentTarget.style.color = '#ccc'}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
        <a href="https://www.linkedin.com/in/jayvk/" target="_blank" rel="noopener noreferrer" style={{ color: '#ccc', transition: 'color 0.2s' }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#0a66c2'} onMouseLeave={(e) => e.currentTarget.style.color = '#ccc'}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
        <a href="https://x.com/jaynotai" target="_blank" rel="noopener noreferrer" style={{ color: '#ccc', transition: 'color 0.2s' }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#000'} onMouseLeave={(e) => e.currentTarget.style.color = '#ccc'}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        * { box-sizing: border-box; }
        input[type=range] { -webkit-appearance: none; background: #e8e8e8; border-radius: 2px; outline: none; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #999; cursor: pointer; }
        ::selection { background: #dbeafe; }
      `}} />
    </div>
  );
}

export default App;
