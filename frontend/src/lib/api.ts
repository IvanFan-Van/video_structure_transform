import axios from "axios";
import { useAuthStore } from "../store/useAuthStore";

function decodeJwtPayload(token: string): Record<string, unknown> | null {
    try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const json = atob(base64);
        return JSON.parse(json);
    } catch {
        return null;
    }
}

export function isTokenExpired(token: string): boolean {
    const payload = decodeJwtPayload(token);
    if (!payload || typeof payload.exp !== "number") return true;
    return payload.exp * 1000 < Date.now();
}

export const apiAxios = axios.create();

apiAxios.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

apiAxios.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            useAuthStore.getState().logout();
        }
        return Promise.reject(error);
    },
);

export async function apiFetch(
    url: string,
    options: RequestInit = {},
): Promise<Response> {
    const token = useAuthStore.getState().token;
    const res = await fetch(url, {
        ...options,
        headers: {
            ...(options.headers as Record<string, string> | undefined),
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
    });
    if (res.status === 401) {
        useAuthStore.getState().logout();
    }
    return res;
}
