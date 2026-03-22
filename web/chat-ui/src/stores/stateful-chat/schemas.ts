import * as z from "zod";

const uuidSchema = z.string().uuid();

export const chatResponseItemSchema = z.object({
    id: uuidSchema,
    owner_subject: z.string(),
    folder_id: z.string().uuid().nullable(),
    title: z.string().nullable(),
    created_at: z.string(),
    updated_at: z.string(),
});
export type ChatResponseItem = z.infer<typeof chatResponseItemSchema>;

export const chatListResponseSchema = z.object({
    items: z.array(chatResponseItemSchema),
    next_cursor: z.string().nullable().optional(),
});
export type ChatListResponse = z.infer<typeof chatListResponseSchema>;

export const chatMessageResponseItemSchema = z.object({
    id: uuidSchema,
    chat_id: uuidSchema,
    role: z.enum(["user", "assistant", "system"]),
    content: z.string(),
    created_at: z.string(),
});
export type ChatMessageResponseItem = z.infer<
    typeof chatMessageResponseItemSchema
>;

export const chatMessageListResponseSchema = z.object({
    items: z.array(chatMessageResponseItemSchema),
    next_cursor: z.string().nullable().optional(),
});
export type ChatMessageListResponse = z.infer<
    typeof chatMessageListResponseSchema
>;

export const addMessageRequestSchema = z.object({
    role: z.enum(["user", "assistant", "system"]),
    content: z.string().min(1).max(65_536),
    generate_reply: z.boolean().optional().default(true),
});
export type AddMessageRequest = z.infer<typeof addMessageRequestSchema>;

export const addMessageResponseSchema = z.object({
    message: chatMessageResponseItemSchema,
    reply: z.string().nullable().optional(),
});
export type AddMessageResponse = z.infer<typeof addMessageResponseSchema>;

export const folderResponseItemSchema = z.object({
    id: uuidSchema,
    owner_subject: z.string(),
    parent_id: z.string().uuid().nullable(),
    name: z.string(),
    system_prompt: z.string().nullable().optional(),
    created_at: z.string(),
    updated_at: z.string(),
});
export type FolderResponseItem = z.infer<typeof folderResponseItemSchema>;

export const folderCreateRequestSchema = z.object({
    name: z.string().min(1).max(255),
    parent_id: uuidSchema.optional().nullable(),
    system_prompt: z.string().optional().nullable(),
});
export type FolderCreateRequest = z.infer<typeof folderCreateRequestSchema>;

export const folderUpdateRequestSchema = z.object({
    name: z.string().min(1).max(255).optional(),
    system_prompt: z.string().optional().nullable(),
});
export type FolderUpdateRequest = z.infer<typeof folderUpdateRequestSchema>;

export const shareResponseItemSchema = z.object({
    chat_id: uuidSchema,
    subject: z.string(),
    role: z.enum(["viewer", "editor"]),
    created_at: z.string(),
    username: z.string().nullable().optional(),
});
export type ShareResponseItem = z.infer<typeof shareResponseItemSchema>;

export const shareRequestSchema = z.object({
    subject_type: z.enum(["user", "service_account", "group"]),
    subject_id: uuidSchema,
    role: z.enum(["viewer", "editor"]),
});
export type ShareRequest = z.infer<typeof shareRequestSchema>;

export const userSearchResponseItemSchema = z.object({
    id: uuidSchema,
    username: z.string(),
});
export type UserSearchResponseItem = z.infer<
    typeof userSearchResponseItemSchema
>;
