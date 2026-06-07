interface ActionButtonProps {
    variant: "primary" | "muted";
    label: string;
    onClick: () => void;
    enabled?: boolean;
    accent?: string;
}

export function ActionButton({
    variant,
    label,
    onClick,
    enabled = true,
    accent = "#333",
}: ActionButtonProps) {
    if (variant === "primary") {
        return (
            <button
                onClick={onClick}
                disabled={!enabled}
                style={{
                    padding: "10px",
                    fontSize: "11px",
                    fontFamily: "inherit",
                    fontWeight: 600,
                    letterSpacing: "1px",
                    color: enabled ? "#fff" : "#bbb",
                    background: enabled ? accent : "#e8e8e8",
                    border: "none",
                    borderRadius: "3px",
                    cursor: enabled ? "pointer" : "not-allowed",
                }}
            >
                {label}
            </button>
        );
    }

    return (
        <button
            onClick={onClick}
            style={{
                padding: "5px",
                fontSize: "9px",
                fontFamily: "inherit",
                background: "transparent",
                border: "1px solid #e0e0e0",
                borderRadius: "3px",
                color: "#999",
                cursor: "pointer",
            }}
        >
            {label}
        </button>
    );
}
