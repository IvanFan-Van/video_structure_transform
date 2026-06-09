interface SelectionRectProps {
    rect: { x: number; y: number; w: number; h: number };
}

export function SelectionRect({ rect }: SelectionRectProps) {
    return (
        <div
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                width: "100vw",
                height: "100vh",
                pointerEvents: "none",
                zIndex: 50,
            }}
        >
            <div
                style={{
                    position: "absolute",
                    left: rect.x,
                    top: rect.y,
                    width: rect.w,
                    height: rect.h,
                    background: "rgba(59,130,246,0.08)",
                    border: "1.5px dashed #3b82f6",
                    borderRadius: "2px",
                }}
            />
        </div>
    );
}
