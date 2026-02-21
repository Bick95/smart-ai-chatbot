import * as z from "zod";

/** Valid message roles */
export const messageRoleSchema = z.enum(["user", "assistant"]);
export type MessageRole = z.infer<typeof messageRoleSchema>;

/** A single chat message */
export const messageSchema = z.object({
    id: z.string().uuid(),
    role: messageRoleSchema,
    content: z.string().min(1).max(65_536),
    createdAt: z.date().optional(),
});
export type Message = z.infer<typeof messageSchema>;

/** New message input (before ID is assigned) */
export const messageInputSchema = z.object({
    role: messageRoleSchema,
    content: z
        .string()
        .min(1, "Message cannot be empty")
        .max(65_536, "Message is too long"),
});
export type MessageInput = z.infer<typeof messageInputSchema>;

/** A chat session with messages */
export const chatSchema = z.object({
    id: z.string().uuid(),
    messages: z.array(messageSchema),
    createdAt: z.date().optional(),
    updatedAt: z.date().optional(),
});
export type Chat = z.infer<typeof chatSchema>;

/** New chat input (before ID/fields are assigned) */
export const chatInputSchema = z.object({
    messages: z.array(messageSchema).optional(),
});
export type ChatInput = z.infer<typeof chatInputSchema>;
