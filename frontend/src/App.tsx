import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Wires } from "./components/ui/Wires";
import { useNodePositions } from "./hooks/useNodePositions";
import { useAppStore } from "./store/useAppStore";
import { useAuthStore } from "./store/useAuthStore";
import { useCanvasStore } from "./store/useCanvasStore";
import { useVideoStore } from "./store/useVideoStore";
import { WIRES } from "./constants";
import { DatasetNode } from "./components/nodes/DatasetNode";
import { TokenizerNode } from "./components/nodes/TokenizerNode";
import { ArchitectureNode } from "./components/nodes/ArchitectureNode";
import { TrainingNode } from "./components/nodes/TrainingNode";
import { MetricsNode } from "./components/nodes/MetricsNode";
import { GenerateNode } from "./components/nodes/GenerateNode";
import { ReferenceNode } from "./components/nodes/ReferenceNode";
import { CompressConfigNode } from "./components/nodes/CompressConfigNode";
import { CompressNode } from "./components/nodes/CompressNode";
import { ExtractingNode } from "./components/nodes/ExtractingNode";
import { ScriptAnalysisNode } from "./components/nodes/ScriptAnalysisNode";
import { AudioAnalysisNode } from "./components/nodes/AudioAnalysisNode";
import { VisualAnalysisNode } from "./components/nodes/VisualAnalysisNode";
import { SplitNode } from "./components/nodes/SplitNode";
import { SplitSegmentNode } from "./components/nodes/SplitSegmentNode";
import { NodeErrorToast } from "./components/ui/NodeErrorToast";
import { useZoom } from "./hooks/useZoom";
import { usePan } from "./hooks/usePan";
import { ZoomContext } from "./context/ZoomContext";

const NODES = {
    reference: ReferenceNode,
    compress_config: CompressConfigNode,
    compress: CompressNode,
    extracting: ExtractingNode,
    split: SplitNode,
    script_analysis: ScriptAnalysisNode,
    audio_analysis: AudioAnalysisNode,
    visual_analysis: VisualAnalysisNode,
};

function App() {
    const { positions, update: updatePos } = useNodePositions();
    const initWorker = useAppStore((s) => s.initWorker);
    const destroyWorker = useAppStore((s) => s.destroyWorker);
    const modelReady = useAppStore((s) => s.modelReady);
    const saveRunHistory = useAppStore((s) => s.saveRunHistory);
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const savePreset = useCanvasStore((s) => s.savePreset);
    const splitResult = useVideoStore((s) => s.splitResult);
    const navigate = useNavigate();
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const [toast, setToast] = useState<string | null>(null);

    useEffect(() => {
        initWorker();
        return () => destroyWorker();
    }, []);

    useEffect(() => {
        if (modelReady) saveRunHistory();
    }, [modelReady, saveRunHistory]);

    useEffect(() => {
        const onClick = (e: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(e.target as Node)
            ) {
                setDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", onClick);
        return () => document.removeEventListener("mousedown", onClick);
    }, []);

    useEffect(() => {
        if (toast) {
            const t = setTimeout(() => setToast(null), 2000);
            return () => clearTimeout(t);
        }
    }, [toast]);

    const zoom = useZoom();
    const { panX, panY, onMouseDown: onPanMouseDown } = usePan(zoom);

    const [offset, setOffset] = useState(60);
    useEffect(() => {
        const calcOffset = () => {
            const totalWidth = 2070;
            const ox = Math.max(
                60,
                Math.floor((window.innerWidth - totalWidth) / 2),
            );
            setOffset(ox);
        };
        calcOffset();
        window.addEventListener("resize", calcOffset);
        return () => window.removeEventListener("resize", calcOffset);
    }, []);

    const allWires = useMemo<[string, string][]>(() => {
        const base = [...WIRES];
        if (splitResult?.segments) {
            for (let i = 0; i < splitResult.segments.length; i++) {
                base.push(["split", `split_segment_${i}`]);
            }
        }
        return base;
    }, [splitResult]);

    return (
        <div
            onMouseDown={onPanMouseDown}
            style={{
                width: "100vw",
                height: "100vh",
                overflow: "hidden",
                position: "relative",
                fontFamily: "'JetBrains Mono', monospace",
                background: "#fafafa",
                backgroundImage:
                    "radial-gradient(circle, #e0e0e0 0.8px, transparent 0.8px)",
                backgroundSize: "20px 20px",
            }}
        >
            <div
                style={{
                    position: "fixed",
                    top: 16,
                    left: 20,
                    zIndex: 100,
                    fontSize: "10px",
                    fontWeight: 700,
                    letterSpacing: "3px",
                    color: "#ccc",
                }}
            >
                VIRAL STYLE
            </div>
            {user && (
                <div
                    ref={dropdownRef}
                    style={{
                        position: "fixed",
                        top: 12,
                        right: 20,
                        zIndex: 100,
                    }}
                >
                    <button
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        style={{
                            fontSize: "10px",
                            fontFamily: "inherit",
                            color: "#555",
                            background: "#fff",
                            border: "1px solid #e0e0e0",
                            borderRadius: "20px",
                            padding: "5px 14px",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                        }}
                    >
                        <span
                            style={{
                                maxWidth: "180px",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                            }}
                        >
                            {user.email}
                        </span>
                        <span style={{ fontSize: "8px", color: "#bbb" }}>
                            ▼
                        </span>
                    </button>
                    {dropdownOpen && (
                        <div
                            style={{
                                position: "absolute",
                                top: "110%",
                                right: 0,
                                background: "#fff",
                                border: "1px solid #e8e8e8",
                                borderRadius: "6px",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                                overflow: "hidden",
                                minWidth: "120px",
                            }}
                        >
                            <button
                                onClick={() => {
                                    savePreset();
                                    setToast("Layout saved");
                                    setDropdownOpen(false);
                                }}
                                style={{
                                    width: "100%",
                                    padding: "8px 16px",
                                    textAlign: "left",
                                    fontSize: "10px",
                                    fontFamily: "inherit",
                                    color: "#666",
                                    background: "transparent",
                                    border: "none",
                                    cursor: "pointer",
                                }}
                                onMouseEnter={(e) =>
                                    (e.currentTarget.style.background =
                                        "#f5f5f5")
                                }
                                onMouseLeave={(e) =>
                                    (e.currentTarget.style.background =
                                        "transparent")
                                }
                            >
                                Save layout
                            </button>
                            <button
                                onClick={() => {
                                    logout();
                                    setDropdownOpen(false);
                                    navigate("/login");
                                }}
                                style={{
                                    width: "100%",
                                    padding: "8px 16px",
                                    textAlign: "left",
                                    fontSize: "10px",
                                    fontFamily: "inherit",
                                    color: "#666",
                                    background: "transparent",
                                    border: "none",
                                    cursor: "pointer",
                                }}
                                onMouseEnter={(e) =>
                                    (e.currentTarget.style.background =
                                        "#f5f5f5")
                                }
                                onMouseLeave={(e) =>
                                    (e.currentTarget.style.background =
                                        "transparent")
                                }
                            >
                                Log out
                            </button>
                        </div>
                    )}
                </div>
            )}

            <div
                style={{
                    position: "fixed",
                    bottom: 16,
                    left: 20,
                    zIndex: 100,
                    fontSize: "10px",
                    color: "#bbb",
                    lineHeight: "1.8",
                    pointerEvents: "none",
                }}
            >
                <div>Ctrl + Scroll &mdash; Zoom</div>
                <div>Drag background &mdash; Pan</div>
                <div>Drag nodes &mdash; Move</div>
            </div>

            <ZoomContext.Provider value={zoom}>
                <Wires
                    positions={positions}
                    wires={allWires}
                    zoom={zoom}
                    panX={panX}
                    panY={panY}
                />
                <div
                    style={{
                        transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
                        transformOrigin: "top left",
                        width: `calc(100% / ${zoom})`,
                        height: `calc(100% / ${zoom})`,
                    }}
                >
                    {/* <DatasetNode x={offset} y={80} onPosChange={updatePos} />
            <TokenizerNode x={offset} y={380} onPosChange={updatePos} />

            <ArchitectureNode x={offset + 310} y={80} onPosChange={updatePos} />
            <TrainingNode x={offset + 310} y={440} onPosChange={updatePos} />

            <MetricsNode x={offset + 640} y={80} onPosChange={updatePos} />
            <GenerateNode x={offset + 640} y={440} onPosChange={updatePos} /> */}

                    <ReferenceNode x={offset} y={30} onPosChange={updatePos} />
                    <CompressConfigNode
                        x={offset + 310}
                        y={30}
                        onPosChange={updatePos}
                    />
                    <CompressNode
                        x={offset + 640}
                        y={30}
                        onPosChange={updatePos}
                    />
                    <ExtractingNode
                        x={offset + 950}
                        y={30}
                        onPosChange={updatePos}
                    />
                    <SplitNode
                        x={offset + 1100}
                        y={30}
                        onPosChange={updatePos}
                    />
                    {splitResult?.segments?.map((seg, i) => (
                        <SplitSegmentNode
                            key={`seg_${i}`}
                            x={offset + 1430}
                            y={30 + i * 200}
                            segment={seg}
                            clip={splitResult.clip_assets?.find(
                                (c) => c.index === i,
                            )}
                            index={i}
                            method={splitResult.method}
                            onPosChange={updatePos}
                        />
                    ))}
                    <ScriptAnalysisNode
                        x={offset + 1260}
                        y={30}
                        onPosChange={updatePos}
                    />
                    <AudioAnalysisNode
                        x={offset + 1570}
                        y={30}
                        onPosChange={updatePos}
                    />
                    <VisualAnalysisNode
                        x={offset + 1880}
                        y={30}
                        onPosChange={updatePos}
                    />

                    <style
                        dangerouslySetInnerHTML={{
                            __html: `
        * { box-sizing: border-box; }
        input[type=range] { -webkit-appearance: none; background: #e8e8e8; border-radius: 2px; outline: none; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #999; cursor: pointer; }
        ::selection { background: #dbeafe; }
      `,
                        }}
                    />
                </div>
            </ZoomContext.Provider>
            {toast && (
                <div
                    style={{
                        position: "fixed",
                        top: 48,
                        right: 20,
                        zIndex: 200,
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "10px",
                        fontFamily: "'JetBrains Mono', monospace",
                        color: "#166534",
                        background: "#f0fdf4",
                        border: "1px solid #bbf7d0",
                        borderRadius: "6px",
                        padding: "8px 14px",
                        boxShadow: "0 2px 8px rgba(34,197,94,0.10)",
                    }}
                >
                    <svg
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#22c55e"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <polyline points="20 6 9 17 4 12" />
                    </svg>
                    {toast}
                </div>
            )}
            <NodeErrorToast />
        </div>
    );
}

export default App;
