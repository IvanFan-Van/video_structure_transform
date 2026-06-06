import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { NodeError } from './types';
import { useVideoStore } from './useVideoStore';

interface User {
    user_id: string;
    email: string;
}

interface AuthState {
    token: string | null;
    user: User | null;
    isAuthenticated: boolean;
    login: (
        email: string,
        password: string,
    ) => Promise<{ success: boolean; error?: string }>;
    register: (
        email: string,
        password: string,
    ) => Promise<{ success: boolean; error?: string }>;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            token: null,
            user: null,
            isAuthenticated: false,

            login: async (email, password) => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), 10000);
                try {
                    const res = await fetch("/api/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, password }),
                        signal: controller.signal,
                    });
                    clearTimeout(timer);
                    const json = await res.json();
                    if (json.status !== "success") {
                        const msg =
                            json.message ||
                            (json.data ? JSON.stringify(json.data) : null) ||
                            "Login failed";
                        return { success: false, error: msg };
                    }
                    set({
                        token: json.data.access_token,
                        user: json.data.user,
                        isAuthenticated: true,
                    });
                    return { success: true };
                } catch (err: any) {
                    clearTimeout(timer);
                    const isTimeout = err?.name === "AbortError";
                    const msg = isTimeout
                        ? "Request timed out"
                        : "Network error";
                    const code = isTimeout ? "TIMEOUT" : "NETWORK_ERROR";
                    const details = isTimeout
                        ? "Login request exceeded 10s timeout"
                        : "Unable to reach the server. Check your connection.";
                    useVideoStore.setState((s) => ({
                        videoErrors: [
                            ...s.videoErrors.filter((e) => e.nodeId !== "auth"),
                            {
                                id: Date.now(),
                                nodeId: "auth",
                                message: msg,
                                code,
                                details,
                            } as NodeError,
                        ],
                    }));
                    return { success: false, error: msg };
                }
            },

            register: async (email, password) => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), 10000);
                try {
                    const res = await fetch("/api/register", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ email, password }),
                        signal: controller.signal,
                    });
                    clearTimeout(timer);
                    const json = await res.json();
                    if (json.status !== "success") {
                        const msg =
                            json.message ||
                            (json.data ? JSON.stringify(json.data) : null) ||
                            "Registration failed";
                        return { success: false, error: msg };
                    }
                    return { success: true };
                } catch (err: any) {
                    clearTimeout(timer);
                    const isTimeout = err?.name === "AbortError";
                    const msg = isTimeout
                        ? "Request timed out"
                        : "Network error";
                    const code = isTimeout ? "TIMEOUT" : "NETWORK_ERROR";
                    const details = isTimeout
                        ? "Registration request exceeded 10s timeout"
                        : "Unable to reach the server. Check your connection.";
                    useVideoStore.setState((s) => ({
                        videoErrors: [
                            ...s.videoErrors.filter((e) => e.nodeId !== "auth"),
                            {
                                id: Date.now(),
                                nodeId: "auth",
                                message: msg,
                                code,
                                details,
                            } as NodeError,
                        ],
                    }));
                    return { success: false, error: msg };
                }
            },

            logout: () =>
                set({ token: null, user: null, isAuthenticated: false }),
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({
                token: state.token,
                user: state.user,
                isAuthenticated: state.isAuthenticated,
            }),
        },
    ),
);
