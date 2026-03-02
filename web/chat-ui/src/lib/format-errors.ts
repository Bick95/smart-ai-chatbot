/**
 * Format a caught error for display.
 */
export function formatCaughtError(err: unknown, fallback: string): string {
    if (err instanceof Error) return err.message;
    if (err && typeof err === "object" && "message" in err) {
        const msg = (err as { message: unknown }).message;
        if (typeof msg === "string") return msg;
    }
    return fallback;
}

/**
 * Format form field errors for display.
 * Handles strings, Error-like objects, and Zod-style issues.
 */
export function formatFieldErrors(errors: unknown[]): string {
    return errors
        .map((e) => {
            if (typeof e === "string") return e;
            if (e && typeof e === "object") {
                if ("message" in e && typeof (e as { message: unknown }).message === "string") {
                    return (e as { message: string }).message;
                }
                if ("msg" in e && typeof (e as { msg: unknown }).msg === "string") {
                    return (e as { msg: string }).msg;
                }
            }
            return null;
        })
        .filter((s): s is string => s != null)
        .join(", ") || "Invalid value";
}
