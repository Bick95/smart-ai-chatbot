"use client";

import { Navigate, useLocation } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/stores/auth";

export interface ProtectedRouteProps {
    children: React.ReactNode;
}

/**
 * Wraps routes that require authentication.
 * Redirects to /login if not signed in (after hydration).
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
    const user = useAuthStore((s) => s.user);
    const isHydrating = useAuthStore((s) => s.isHydrating);
    const location = useLocation();

    if (isHydrating) {
        return (
            <div className="flex h-dvh flex-col items-center justify-center gap-4 bg-background p-6">
                <div className="flex flex-col gap-3">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-64" />
                    <Skeleton className="mt-4 h-4 w-32" />
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <>{children}</>;
}
