"use client";

import { useAuthStore } from "@/stores/auth";

export function DashboardPage() {
    const user = useAuthStore((s) => s.user);

    return (
        <div className="flex flex-col gap-6 p-6">
            <h1 className="text-2xl font-semibold">Dashboard</h1>
            {user && (
                <p className="text-muted-foreground">
                    Welcome, {user.username}. Your account is connected.
                </p>
            )}
        </div>
    );
}
