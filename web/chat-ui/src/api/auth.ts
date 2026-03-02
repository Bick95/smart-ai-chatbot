import { API_BASE } from "@/constants";
import type { AuthTokensResponse } from "@/stores/auth/schemas";
import { authTokensResponseSchema } from "@/stores/auth/schemas";

/** Extract a user-facing message from FastAPI-style error detail (string or array of {msg}). */
function formatApiErrorDetail(detail: unknown): string {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        const msgs = detail
            .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : null))
            .filter(Boolean);
        return msgs.length > 0 ? msgs.join(" ") : "Request failed";
    }
    return "Request failed";
}

export interface SignupPayload {
    email: string;
    username: string;
    password: string;
    invite_key?: string;
}

export interface LoginPayload {
    email: string;
    password: string;
}

export async function signup(payload: SignupPayload): Promise<AuthTokensResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Signup failed (${res.status})`;
        throw new Error(message);
    }

    const json: unknown = await res.json();
    return authTokensResponseSchema.parse(json);
}

export async function login(payload: LoginPayload): Promise<AuthTokensResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Login failed (${res.status})`;
        throw new Error(message);
    }

    const json: unknown = await res.json();
    return authTokensResponseSchema.parse(json);
}

export async function refreshToken(
    refreshToken: string
): Promise<AuthTokensResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Token refresh failed (${res.status})`;
        throw new Error(message);
    }

    const json: unknown = await res.json();
    return authTokensResponseSchema.parse(json);
}
