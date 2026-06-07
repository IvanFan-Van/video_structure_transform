import { ReactNode } from "react";

interface AccordionItemProps {
    open: boolean;
    onToggle: () => void;
    title: ReactNode;
    subtitle?: string;
    accent?: string;
    accentBg?: string;
    accentBorder?: string;
    children: ReactNode;
}

export function AccordionItem({
    open,
    onToggle,
    title,
    subtitle,
    accent,
    accentBg,
    accentBorder,
    children,
}: AccordionItemProps) {
    return (
        <div>
            <div
                onClick={onToggle}
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "5px 8px",
                    borderRadius: "3px",
                    background: open ? (accentBg ?? "#fafafa") : "#fafafa",
                    border: open
                        ? accentBorder
                            ? `1px solid ${accentBorder}`
                            : "1px solid #f0f0f0"
                        : "1px solid #f0f0f0",
                    cursor: "pointer",
                    transition: "background 0.15s, border-color 0.15s",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "9px",
                        fontWeight: 600,
                        color: open ? (accent ?? "#555") : "#555",
                    }}
                >
                    <span
                        style={{
                            fontSize: "8px",
                            color: open ? (accent ?? "#555") : "#bbb",
                            fontWeight: 400,
                        }}
                    >
                        {open ? "\u25bc" : "\u25b6"}
                    </span>
                    {title}
                </div>
                {subtitle && (
                    <span style={{ fontSize: "8px", color: "#bbb" }}>
                        {subtitle}
                    </span>
                )}
            </div>
            {open && (
                <div
                    style={{
                        marginTop: "4px",
                        padding: "8px",
                        background: "#fafafa",
                        borderRadius: "3px",
                        border: "1px solid #f0f0f0",
                        fontSize: "8px",
                        color: "#555",
                        lineHeight: "1.6",
                    }}
                >
                    {children}
                </div>
            )}
        </div>
    );
}
