import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";
import { isTokenExpired } from "../lib/api";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
    const token = useAuthStore((s) => s.token);

    useEffect(() => {
        if (token && isTokenExpired(token)) {
            useAuthStore.getState().logout();
        }
    }, [token]);

    if (!isAuthenticated) return <Navigate to="/login" replace />;
    return <>{children}</>;
}
