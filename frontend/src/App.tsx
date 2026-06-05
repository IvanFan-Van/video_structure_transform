import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Wires } from "./components/ui/Wires";
import { useAppStore } from "./store/useAppStore";
import { useAuthStore } from "./store/useAuthStore";
import { useUIStore } from "./store/useUIStore";
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
import { NodeErrorToast } from "./components/ui/NodeErrorToast";

function App() {
    const initWorker = useAppStore((s) => s.initWorker);
    const destroyWorker = useAppStore((s) => s.destroyWorker);
    const modelReady = useAppStore((s) => s.modelReady);
    const saveRunHistory = useAppStore((s) => s.saveRunHistory);
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const navigate = useNavigate();
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const zoom = useUIStore((s) => s.zoom);
    const panX = useUIStore((s) => s.panX);
    const panY = useUIStore((s) => s.panY);
    const positions = useUIStore((s) => s.nodePositions);
    const postionsTick = useUIStore((s) => s.positionTick);
    const updatePos = useUIStore((s) => s.updateNodePosition);

    const panDrag = useRef(false);
    const panLast = useRef({ x: 0, y: 0 });

    const onPanMouseDown = useCallback((e: React.MouseEvent) => {
        if (
            ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(
                (e.target as HTMLElement).tagName,
            )
        )
            return;
        panDrag.current = true;
        panLast.current = { x: e.clientX, y: e.clientY };
        e.preventDefault();
    }, []);

    useEffect(() => {
        const mv = (e: MouseEvent) => {
            if (!panDrag.current) return;
            const dx = e.clientX - panLast.current.x;
            const dy = e.clientY - panLast.current.y;
            panLast.current = { x: e.clientX, y: e.clientY };
            useUIStore.getState().addPanDelta(dx, dy);
        };
        const up = () => {
            panDrag.current = false;
        };
        window.addEventListener("mousemove", mv);
        window.addEventListener("mouseup", up);
        return () => {
            window.removeEventListener("mousemove", mv);
            window.removeEventListener("mouseup", up);
        };
    }, []);

    useEffect(() => {
        const onWheel = (e: WheelEvent) => {
            if (!e.ctrlKey && !e.metaKey) return;
            e.preventDefault();
            const z = useUIStore.getState().zoom;
            const next = z - e.deltaY * 0.001;
            useUIStore.getState().setZoom(next);
        };
        window.addEventListener("wheel", onWheel, { passive: false });
        return () => window.removeEventListener("wheel", onWheel);
    }, []);

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
                TRAIN MY OWN GPT
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

            <Wires
                wires={WIRES}
                zoom={zoom}
                panX={panX}
                panY={panY}
                positions={positions}
                tick={postionsTick}
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
                <CompressNode x={offset + 640} y={30} onPosChange={updatePos} />
                <ExtractingNode
                    x={offset + 950}
                    y={30}
                    onPosChange={updatePos}
                />
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
            <NodeErrorToast />
        </div>
    );
}

export default App;
