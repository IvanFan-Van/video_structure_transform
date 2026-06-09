import { useState, useCallback } from "react";

const TOUR_KEY = "tour-seen-v1";

export function useTour() {
    const [seen, setSeen] = useState(() => {
        try {
            return localStorage.getItem(TOUR_KEY) === "1";
        } catch {
            return false;
        }
    });

    const markSeen = useCallback(() => {
        try {
            localStorage.setItem(TOUR_KEY, "1");
        } catch {}
        setSeen(true);
    }, []);

    const reset = useCallback(() => {
        try {
            localStorage.removeItem(TOUR_KEY);
        } catch {}
        setSeen(false);
    }, []);

    return { seen, markSeen, reset };
}
