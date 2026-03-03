"use client";

import { useState } from "react";
import { useForm } from "@tanstack/react-form";
import * as z from "zod";

import {
    deleteUser,
    updateEmail,
    updatePassword,
    updateUsername,
} from "@/api/auth";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
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
import { formatCaughtError, formatFieldErrors } from "@/lib/format-errors";
import { useAuthStore } from "@/stores/auth";

const usernameSchema = z.object({
    username: z
        .string()
        .min(1, "Username required")
        .max(255)
        .regex(
            /^[a-zA-Z0-9_-]+$/,
            "Username must contain only letters, numbers, underscores, and hyphens"
        ),
});

const emailSchema = z.object({
    email: z.string().min(5, "Email required").max(255).email("Invalid email"),
});

const passwordSchema = z
    .object({
        password: z
            .string()
            .min(8, "Password must be at least 8 characters")
            .max(128, "Password must be at most 128 characters"),
        confirmPassword: z.string().min(1, "Please confirm your password"),
    })
    .refine((data) => data.password === data.confirmPassword, {
        message: "Passwords do not match",
        path: ["confirmPassword"],
    });

export function DashboardPage() {
    const user = useAuthStore((s) => s.user);
    const authToken = useAuthStore((s) => s.authToken);
    const updateUser = useAuthStore((s) => s.updateUser);
    const clearAuth = useAuthStore((s) => s.clearAuth);
    const [usernameError, setUsernameError] = useState<string | null>(null);
    const [usernameSuccess, setUsernameSuccess] = useState<string | null>(null);
    const [usernameLoading, setUsernameLoading] = useState(false);

    const [emailError, setEmailError] = useState<string | null>(null);
    const [emailSuccess, setEmailSuccess] = useState<string | null>(null);
    const [emailLoading, setEmailLoading] = useState(false);

    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
    const [passwordLoading, setPasswordLoading] = useState(false);

    const usernameForm = useForm({
        defaultValues: { username: user?.username ?? "" },
        validators: { onSubmit: usernameSchema },
        onSubmit: async ({ value }) => {
            if (!user?.id || !authToken) {
                setUsernameError("ID or credentials missing. Please refresh page.");
                return;
            }
            setUsernameError(null);
            setUsernameSuccess(null);
            setUsernameLoading(true);
            try {
                const updated = await updateUsername(user.id, value.username, authToken);
                updateUser(updated);
                setUsernameSuccess("Username updated.");
            } catch (err) {
                setUsernameError(formatCaughtError(err, "Username update failed"));
            } finally {
                setUsernameLoading(false);
            }
        },
    });

    const emailForm = useForm({
        defaultValues: { email: user?.email ?? "" },
        validators: { onSubmit: emailSchema },
        onSubmit: async ({ value }) => {
            if (!user?.id || !authToken) {
                setEmailError("ID or credentials missing. Please refresh page.");
                return;
            }
            setEmailError(null);
            setEmailSuccess(null);
            setEmailLoading(true);
            try {
                const updated = await updateEmail(user.id, value.email, authToken);
                updateUser(updated);
                setEmailSuccess("Email updated.");
            } catch (err) {
                setEmailError(formatCaughtError(err, "Email update failed"));
            } finally {
                setEmailLoading(false);
            }
        },
    });

    const passwordForm = useForm({
        defaultValues: { password: "", confirmPassword: "" },
        validators: { onSubmit: passwordSchema },
        onSubmit: async ({ value }) => {
            if (!user?.id || !authToken) {
                setPasswordError("ID or credentials missing. Please refresh page.");
                return;
            }
            setPasswordError(null);
            setPasswordSuccess(null);
            setPasswordLoading(true);
            try {
                await updatePassword(user.id, value.password, authToken);
                setPasswordSuccess("Password updated.");
                passwordForm.reset();
            } catch (err) {
                setPasswordError(formatCaughtError(err, "Password update failed"));
            } finally {
                setPasswordLoading(false);
            }
        },
    });

    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState<string | null>(null);

    const handleDeleteAccount = async () => {
        if (!user?.id || !authToken) {
            setDeleteError("ID or credentials missing. Please refresh page.");
            return;
        }
        setDeleteError(null);
        setIsDeleting(true);
        try {
            await deleteUser(user.id, authToken);
            clearAuth();
            setDeleteDialogOpen(false);
            window.location.href = "/login";
        } catch (err) {
            setDeleteError(formatCaughtError(err, "Account deletion failed"));
        } finally {
            setIsDeleting(false);
        }
    };

    if (!user) {
        return (
            <div className="flex flex-col gap-4 p-6">
                <h1 className="text-2xl font-semibold">Dashboard</h1>
                <p className="text-muted-foreground">Please sign in to manage your account if you have one.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 p-6">
            <div>
                <h1 className="text-2xl font-semibold">Dashboard</h1>
                <p className="text-muted-foreground">
                    Manage your account settings.
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Profile</CardTitle>
                    <CardDescription>
                        Your account information.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                    <div>
                        <span className="text-muted-foreground text-sm">Username:</span>{" "}
                        {user.username}
                    </div>
                    <div>
                        <span className="text-muted-foreground text-sm">Email:</span>{" "}
                        {user.email}
                    </div>
                    <div>
                        <span className="text-muted-foreground text-sm">ID:</span>{" "}
                        <code className="text-muted-foreground text-xs">{user.id}</code>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Update username</CardTitle>
                    <CardDescription>
                        Change your display name.
                    </CardDescription>
                </CardHeader>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        void usernameForm.handleSubmit();
                    }}
                >
                    <CardContent className="space-y-4">
                        {usernameError && (
                            <Alert variant="destructive">
                                <AlertDescription>{usernameError}</AlertDescription>
                            </Alert>
                        )}
                        {usernameSuccess && (
                            <Alert variant="success">
                                <AlertDescription>{usernameSuccess}</AlertDescription>
                            </Alert>
                        )}
                        <usernameForm.Field
                            name="username"
                            children={(field) => (
                                <div className="space-y-2">
                                    <Label htmlFor={field.name}>Username</Label>
                                    <Input
                                        id={field.name}
                                        value={field.state.value}
                                        onChange={(e) =>
                                            field.handleChange(e.target.value)
                                        }
                                        onBlur={field.handleBlur}
                                        placeholder="johndoe"
                                        autoComplete="username"
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
                    <CardFooter>
                        <Button
                            type="submit"
                            disabled={usernameLoading}
                        >
                            {usernameLoading ? "Updating…" : "Update username"}
                        </Button>
                    </CardFooter>
                </form>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Update email</CardTitle>
                    <CardDescription>
                        Change your email address.
                    </CardDescription>
                </CardHeader>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        void emailForm.handleSubmit();
                    }}
                >
                    <CardContent className="space-y-4">
                        {emailError && (
                            <Alert variant="destructive">
                                <AlertDescription>{emailError}</AlertDescription>
                            </Alert>
                        )}
                        {emailSuccess && (
                            <Alert variant="success">
                                <AlertDescription>{emailSuccess}</AlertDescription>
                            </Alert>
                        )}
                        <emailForm.Field
                            name="email"
                            children={(field) => (
                                <div className="space-y-2">
                                    <Label htmlFor={field.name}>Email</Label>
                                    <Input
                                        id={field.name}
                                        type="email"
                                        value={field.state.value}
                                        onChange={(e) =>
                                            field.handleChange(e.target.value)
                                        }
                                        onBlur={field.handleBlur}
                                        placeholder="you@example.com"
                                        autoComplete="email"
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
                    <CardFooter>
                        <Button
                            type="submit"
                            disabled={emailLoading}
                        >
                            {emailLoading ? "Updating…" : "Update email"}
                        </Button>
                    </CardFooter>
                </form>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Update password</CardTitle>
                    <CardDescription>
                        Set a new password.
                    </CardDescription>
                </CardHeader>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        void passwordForm.handleSubmit();
                    }}
                >
                    <CardContent className="space-y-4">
                        {passwordError && (
                            <Alert variant="destructive">
                                <AlertDescription>{passwordError}</AlertDescription>
                            </Alert>
                        )}
                        {passwordSuccess && (
                            <Alert variant="success">
                                <AlertDescription>{passwordSuccess}</AlertDescription>
                            </Alert>
                        )}
                        <passwordForm.Field
                            name="password"
                            children={(field) => (
                                <div className="space-y-2">
                                    <Label htmlFor={field.name}>New password</Label>
                                    <Input
                                        id={field.name}
                                        type="password"
                                        value={field.state.value}
                                        onChange={(e) =>
                                            field.handleChange(e.target.value)
                                        }
                                        onBlur={field.handleBlur}
                                        placeholder="••••••••"
                                        autoComplete="new-password"
                                    />
                                    {field.state.meta.errors.length > 0 && (
                                        <p className="text-destructive text-xs">
                                            {formatFieldErrors(field.state.meta.errors)}
                                        </p>
                                    )}
                                </div>
                            )}
                        />
                        <passwordForm.Field
                            name="confirmPassword"
                            children={(field) => (
                                <div className="space-y-2">
                                    <Label htmlFor={field.name}>
                                        Confirm new password
                                    </Label>
                                    <Input
                                        id={field.name}
                                        type="password"
                                        value={field.state.value}
                                        onChange={(e) =>
                                            field.handleChange(e.target.value)
                                        }
                                        onBlur={field.handleBlur}
                                        placeholder="••••••••"
                                        autoComplete="new-password"
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
                    <CardFooter>
                        <Button
                            type="submit"
                            disabled={passwordLoading}
                        >
                            {passwordLoading ? "Updating…" : "Update password"}
                        </Button>
                    </CardFooter>
                </form>
            </Card>

            <Card className="border-destructive/50">
                <CardHeader>
                    <CardTitle className="text-destructive">Delete account</CardTitle>
                    <CardDescription>
                        Permanently delete your account and all associated data.
                        This action cannot be undone.
                    </CardDescription>
                </CardHeader>
                <CardFooter>
                    <AlertDialog
                        open={deleteDialogOpen}
                        onOpenChange={(open) => {
                            setDeleteDialogOpen(open);
                            if (!open) setDeleteError(null);
                        }}
                    >
                        <AlertDialogTrigger asChild>
                            <Button variant="destructive">Delete account</Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                            {deleteError && (
                                <Alert variant="destructive" className="mb-4">
                                    <AlertDescription>{deleteError}</AlertDescription>
                                </Alert>
                            )}
                            <AlertDialogHeader>
                                <AlertDialogTitle>Delete account?</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This will permanently delete your account and
                                    all associated data. You will need to sign up
                                    again to use the service.
                                </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                                <AlertDialogCancel disabled={isDeleting}>
                                    Cancel
                                </AlertDialogCancel>
                                <AlertDialogAction
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleDeleteAccount();
                                    }}
                                    disabled={isDeleting}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                    {isDeleting ? "Deleting…" : "Delete account"}
                                </AlertDialogAction>
                            </AlertDialogFooter>
                        </AlertDialogContent>
                    </AlertDialog>
                </CardFooter>
            </Card>
        </div>
    );
}
