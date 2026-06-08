interface StatusHeaderProps {
    variant: "idle" | "loading" | "success" | "error";
    label: string;
    accent?: string;
}

export function StatusHeader({
    variant,
    label,
    accent = "#555",
}: StatusHeaderProps) {
    if (variant === "idle") {
        return (
            <div
                style={{
                    fontSize: "9px",
                    color: "#bbb",
                    textAlign: "center",
                    padding: "12px 0",
                }}
            >
                {label}
            </div>
        );
    }

    const color = variant === "error" ? "#ef4444" : accent;
    const prefix =
        variant === "success" ? "✓ " : variant === "error" ? "✕ " : "";

    return (
        <div
            style={{
                fontSize: "10px",
                fontWeight: 600,
                color,
                letterSpacing: "2px",
                textAlign: "center",
                marginBottom: "2px",
            }}
        >
            {prefix}
            {label}
        </div>
    );
}
