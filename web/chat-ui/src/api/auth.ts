import { API_BASE } from "@/constants";
import type { AuthTokensResponse, AuthUser } from "@/stores/auth/schemas";
import { authTokensResponseSchema, authUserSchema } from "@/stores/auth/schemas";

export type AuthUserResponse = AuthUser;

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

export async function getUser(userId: string, authToken: string): Promise<AuthUserResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/users/${userId}`, {
        headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Failed to load user (${res.status})`;
        throw new Error(message);
    }
    const json: unknown = await res.json();
    return authUserSchema.parse(json);
}

export async function updateUsername(
    userId: string,
    username: string,
    authToken: string
): Promise<AuthUserResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/users/${userId}/username`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ username }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Username update failed (${res.status})`;
        throw new Error(message);
    }
    const json: unknown = await res.json();
    return authUserSchema.parse(json);
}

export async function updateEmail(
    userId: string,
    email: string,
    authToken: string
): Promise<AuthUserResponse> {
    const res = await fetch(`${API_BASE}/api/v1/auth/users/${userId}/email`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Email update failed (${res.status})`;
        throw new Error(message);
    }
    const json: unknown = await res.json();
    return authUserSchema.parse(json);
}

export async function updatePassword(
    userId: string,
    password: string,
    authToken: string
): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/auth/users/${userId}/password`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ password }),
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Password update failed (${res.status})`;
        throw new Error(message);
    }
}

export async function deleteUser(userId: string, authToken: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/auth/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const message = data.detail != null ? formatApiErrorDetail(data.detail) : `Account deletion failed (${res.status})`;
        throw new Error(message);
    }
}
