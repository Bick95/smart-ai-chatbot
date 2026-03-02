import { create } from "zustand";
import { persist } from "zustand/middleware";

import { refreshToken } from "@/api/auth";
import type { AuthUser } from "./schemas";

const AUTH_STORAGE_KEY = "chat-ui-auth";

interface AuthState {
    user: AuthUser | null;
    authToken: string | null;
    refreshTokenValue: string | null;
    /** True while checking/refreshing token on init */
    isHydrating: boolean;
}

interface AuthActions {
    setAuth: (user: AuthUser, authToken: string, refreshTokenValue: string) => void;
    clearAuth: () => void;
    /** Refresh tokens; updates store on success, clears on failure */
    refreshAuth: () => Promise<boolean>;
    /** Call on app init to restore session from storage and optionally refresh */
    hydrate: () => Promise<void>;
}

const initialState: AuthState = {
    user: null,
    authToken: null,
    refreshTokenValue: null,
    isHydrating: true,
};

export const useAuthStore = create<AuthState & AuthActions>()(
    persist(
        (set, get) => ({
            ...initialState,

            setAuth: (user, authToken, refreshTokenValue) => {
                set({
                    user,
                    authToken,
                    refreshTokenValue,
                    isHydrating: false,
                });
            },

            clearAuth: () => {
                set({
                    user: null,
                    authToken: null,
                    refreshTokenValue: null,
                    isHydrating: false,
                });
            },

            refreshAuth: async () => {
                const { refreshTokenValue } = get();
                if (!refreshTokenValue) return false;

                try {
                    const data = await refreshToken(refreshTokenValue);
                    set({
                        user: data.user,
                        authToken: data.auth_token,
                        refreshTokenValue: data.refresh_token,
                    });
                    return true;
                } catch {
                    get().clearAuth();
                    return false;
                }
            },

            hydrate: async () => {
                const { refreshTokenValue } = get();
                if (!refreshTokenValue) {
                    set({ isHydrating: false });
                    return;
                }

                try {
                    await get().refreshAuth();
                } catch {
                    // refreshAuth already clears on failure
                } finally {
                    set({ isHydrating: false });
                }
            },
        }),
        {
            name: AUTH_STORAGE_KEY,
            partialize: (s) => ({
                user: s.user,
                authToken: s.authToken,
                refreshTokenValue: s.refreshTokenValue,
            }),
        }
    )
);
