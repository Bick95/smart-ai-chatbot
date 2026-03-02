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
import { signup } from "@/api/auth";
import { formatCaughtError, formatFieldErrors } from "@/lib/format-errors";
import { useAuthStore } from "@/stores/auth";

const signupSchema = z.object({
    email: z.string().min(5, "Email required").max(255).email("Invalid email"),
    username: z.string().min(1, "Username required").max(255),
    password: z.string().min(8, "Password must be at least 8 characters").max(128),
    invite_key: z.string(),
});

export interface SignupFormProps {
    onSuccess?: () => void;
    onSwitchToLogin?: () => void;
}

export function SignupForm({ onSuccess, onSwitchToLogin }: SignupFormProps) {
    const [error, setError] = useState<string | null>(null);
    const setAuth = useAuthStore((s) => s.setAuth);

    const form = useForm({
        defaultValues: {
            email: "",
            username: "",
            password: "",
            invite_key: "",
        },
        validators: { onSubmit: signupSchema },
        onSubmit: async ({ value }) => {
            setError(null);
            try {
                const payload = {
                    email: value.email,
                    username: value.username,
                    password: value.password,
                    ...(value.invite_key?.trim()
                        ? { invite_key: value.invite_key.trim() }
                        : {}),
                };
                const data = await signup(payload);
                setAuth(data.user, data.auth_token, data.refresh_token);
                onSuccess?.();
            } catch (err) {
                setError(formatCaughtError(err, "Signup failed"));
            }
        },
    });

    return (
        <Card className="w-full max-w-sm">
            <CardHeader className="space-y-1">
                <CardTitle className="text-2xl">Create an account</CardTitle>
                <CardDescription>
                    Enter your details to get started.
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
                        name="username"
                        children={(field) => (
                            <div className="space-y-2">
                                <Label htmlFor={field.name}>Username</Label>
                                <Input
                                    id={field.name}
                                    type="text"
                                    name={field.name}
                                    value={field.state.value}
                                    onBlur={field.handleBlur}
                                    onChange={(e) =>
                                        field.handleChange(e.target.value)
                                    }
                                    placeholder="johndoe"
                                    autoComplete="username"
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
                                    autoComplete="new-password"
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
                        name="invite_key"
                        children={(field) => (
                            <div className="space-y-2">
                                <Label htmlFor={field.name}>
                                    Invite key{" "}
                                    <span className="text-muted-foreground font-normal">
                                        (if required)
                                    </span>
                                </Label>
                                <Input
                                    id={field.name}
                                    type="password"
                                    name={field.name}
                                    value={field.state.value}
                                    onBlur={field.handleBlur}
                                    onChange={(e) =>
                                        field.handleChange(e.target.value)
                                    }
                                    placeholder="Enter invite key if you have one"
                                    autoComplete="off"
                                />
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
                        {form.state.isSubmitting
                            ? "Creating account…"
                            : "Sign up"}
                    </Button>
                    {onSwitchToLogin && (
                        <p className="text-muted-foreground text-center text-sm">
                            Already have an account?{" "}
                            <button
                                type="button"
                                onClick={onSwitchToLogin}
                                className="text-primary hover:underline font-medium"
                            >
                                Sign in
                            </button>
                        </p>
                    )}
                </CardFooter>
            </form>
        </Card>
    );
}
