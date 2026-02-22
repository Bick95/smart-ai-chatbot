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

// --- API wire schemas (request/response validation) ---

/**
 * Message roles accepted by the chat API.
 * Differs from messageRoleSchema above: the API supports "system" for system prompts
 * (backend allows it at the start of a conversation); the store only tracks
 * user/assistant since that's what the UI displays.
 */
export const chatApiMessageRoleSchema = z.enum(["user", "assistant", "system"]);
export type ChatApiMessageRole = z.infer<typeof chatApiMessageRoleSchema>;

/** Single message in API request body */
export const chatApiMessageSchema = z.object({
    role: chatApiMessageRoleSchema,
    content: z.string().min(1).max(65_536),
});
export type ChatApiMessage = z.infer<typeof chatApiMessageSchema>;

/** Request body for stateless chat endpoint */
export const chatApiRequestSchema = z.object({
    messages: z.array(chatApiMessageSchema).min(1),
});
export type ChatApiRequest = z.infer<typeof chatApiRequestSchema>;

/** Response from stateless chat endpoint */
export const chatApiResponseSchema = z.object({
    content: z.string(),
});
export type ChatApiResponse = z.infer<typeof chatApiResponseSchema>;
