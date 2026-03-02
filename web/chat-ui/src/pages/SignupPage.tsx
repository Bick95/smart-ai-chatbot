"use client";

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { SignupForm } from "@/components/auth";
import { useAuthStore } from "@/stores/auth";

export function SignupPage() {
    const navigate = useNavigate();
    const user = useAuthStore((s) => s.user);
    const isHydrating = useAuthStore((s) => s.isHydrating);

    useEffect(() => {
        if (!isHydrating && user) {
            navigate("/", { replace: true });
        }
    }, [user, isHydrating, navigate]);

    if (isHydrating) {
        return (
            <div className="flex h-dvh items-center justify-center">
                <div className="size-6 animate-spin rounded-full border-2 border-current border-t-transparent" />
            </div>
        );
    }

    if (user) {
        return (
            <div className="flex h-dvh items-center justify-center">
                <div className="size-6 animate-spin rounded-full border-2 border-current border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="flex h-dvh flex-col items-center justify-center bg-background p-6">
            <SignupForm
                onSuccess={() => navigate("/", { replace: true })}
                onSwitchToLogin={() => navigate("/login")}
            />
        </div>
    );
}
