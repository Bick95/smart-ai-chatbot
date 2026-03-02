import { API_BASE } from "@/constants";
import type { AuthTokensResponse } from "@/stores/auth/schemas";
import { authTokensResponseSchema } from "@/stores/auth/schemas";

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
        throw new Error(data.detail ?? `Signup failed (${res.status})`);
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
        throw new Error(data.detail ?? `Login failed (${res.status})`);
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
        throw new Error(data.detail ?? `Token refresh failed (${res.status})`);
    }

    const json: unknown = await res.json();
    return authTokensResponseSchema.parse(json);
}
