import { useState, useRef, useEffect, ReactNode } from "react";

interface TooltipProps {
    tip: string;
    inline?: boolean;
    children: ReactNode;
}

export function Tooltip({ tip, inline, children }: TooltipProps) {
    const [show, setShow] = useState(false);
    const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const wrapperRef = useRef<HTMLSpanElement>(null);
    const [above, setAbove] = useState(true);

    useEffect(() => {
        return () => {
            if (timer.current) clearTimeout(timer.current);
        };
    }, []);

    const enter = () => {
        timer.current = setTimeout(() => {
            // Check if there's room above
            if (wrapperRef.current) {
                const rect = wrapperRef.current.getBoundingClientRect();
                setAbove(rect.top > 56);
            }
            setShow(true);
        }, 300);
    };

    const leave = () => {
        if (timer.current) clearTimeout(timer.current);
        setShow(false);
    };

    return (
        <span
            ref={wrapperRef}
            onMouseEnter={enter}
            onMouseLeave={leave}
            style={{ position: "relative", display: inline ? "inline-flex" : "block" }}
        >
            {inline ? children : <div style={{ display: "flex", flexDirection: "column" }}>{children}</div>}
            {show && (
                <span
                    style={{
                        position: "absolute",
                        left: "50%",
                        transform: "translateX(-50%)",
                        [above ? "bottom" : "top"]: "100%",
                        marginTop: above ? 0 : 6,
                        marginBottom: above ? 6 : 0,
                        padding: "5px 10px",
                        background: "#333",
                        color: "#f5f5f5",
                        fontSize: "9px",
                        fontFamily: "'JetBrains Mono', monospace",
                        lineHeight: "1.5",
                        borderRadius: "4px",
                        whiteSpace: "pre-wrap",
                        maxWidth: "220px",
                        width: "max-content",
                        zIndex: 9999,
                        pointerEvents: "none",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.18)",
                        textAlign: "left",
                    }}
                >
                    {tip}
                </span>
            )}
        </span>
    );
}
