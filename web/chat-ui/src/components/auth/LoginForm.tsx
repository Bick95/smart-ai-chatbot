"use client";

import { useState } from "react";
import { useForm } from "@tanstack/react-form";
import * as z from "zod";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/api/auth";
import { formatCaughtError, formatFieldErrors } from "@/lib/format-errors";
import { useAuthStore } from "@/stores/auth";

const loginSchema = z.object({
    email: z.string().min(5, "Email required").max(255),
    password: z.string().min(8, "Password must be at least 8 characters").max(128),
});

export interface LoginFormProps {
    onSuccess?: () => void;
    onSwitchToSignup?: () => void;
}

export function LoginForm({ onSuccess, onSwitchToSignup }: LoginFormProps) {
    const [error, setError] = useState<string | null>(null);
    const setAuth = useAuthStore((s) => s.setAuth);

    const form = useForm({
        defaultValues: { email: "", password: "" },
        validators: { onSubmit: loginSchema },
        onSubmit: async ({ value }) => {
            setError(null);
            try {
                const data = await login(value);
                setAuth(data.user, data.auth_token, data.refresh_token);
                onSuccess?.();
            } catch (err) {
                setError(formatCaughtError(err, "Login failed"));
            }
        },
    });

    return (
        <Card className="w-full max-w-sm">
            <CardHeader className="space-y-1">
                <CardTitle className="text-2xl">Sign in</CardTitle>
                <CardDescription>
                    Enter your credentials to access your account.
                </CardDescription>
            </CardHeader>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    form.handleSubmit();
                }}
            >
                <CardContent className="space-y-4">
                    {error && (
                        <Alert variant="destructive">
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    )}

                    <form.Field
                        name="email"
                        children={(field) => (
                            <div className="space-y-2">
                                <Label htmlFor={field.name}>Email</Label>
                                <Input
                                    id={field.name}
                                    type="email"
                                    name={field.name}
                                    value={field.state.value}
                                    onBlur={field.handleBlur}
                                    onChange={(e) =>
                                        field.handleChange(e.target.value)
                                    }
                                    placeholder="you@example.com"
                                    autoComplete="email"
                                    aria-invalid={
                                        field.state.meta.errors.length > 0
                                    }
                                />
                                {field.state.meta.errors.length > 0 && (
                                    <p className="text-destructive text-xs">
                                        {formatFieldErrors(field.state.meta.errors)}
                                    </p>
                                )}
                            </div>
                        )}
                    />

                    <form.Field
                        name="password"
                        children={(field) => (
                            <div className="space-y-2">
                                <Label htmlFor={field.name}>Password</Label>
                                <Input
                                    id={field.name}
                                    type="password"
                                    name={field.name}
                                    value={field.state.value}
                                    onBlur={field.handleBlur}
                                    onChange={(e) =>
                                        field.handleChange(e.target.value)
                                    }
                                    placeholder="••••••••"
                                    autoComplete="current-password"
                                    aria-invalid={
                                        field.state.meta.errors.length > 0
                                    }
                                />
                                {field.state.meta.errors.length > 0 && (
                                    <p className="text-destructive text-xs">
                                        {formatFieldErrors(field.state.meta.errors)}
                                    </p>
                                )}
                            </div>
                        )}
                    />
                </CardContent>
                <CardFooter className="flex flex-col gap-4">
                    <Button
                        type="submit"
                        className="w-full"
                        disabled={form.state.isSubmitting}
                    >
                        {form.state.isSubmitting ? "Signing in…" : "Sign in"}
                    </Button>
                    {onSwitchToSignup && (
                        <p className="text-muted-foreground text-center text-sm">
                            Don&apos;t have an account?{" "}
                            <button
                                type="button"
                                onClick={onSwitchToSignup}
                                className="text-primary hover:underline font-medium"
                            >
                                Sign up
                            </button>
                        </p>
                    )}
                </CardFooter>
            </form>
        </Card>
    );
}
