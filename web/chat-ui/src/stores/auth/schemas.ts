import * as z from "zod";

export const authUserSchema = z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    username: z.string().min(1),
    created_at: z.string().nullable().optional(),
});
export type AuthUser = z.infer<typeof authUserSchema>;

export const authTokensResponseSchema = z.object({
    user: authUserSchema,
    auth_token: z.string().min(1),
    refresh_token: z.string().min(1),
});
export type AuthTokensResponse = z.infer<typeof authTokensResponseSchema>;
