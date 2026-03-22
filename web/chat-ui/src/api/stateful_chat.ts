import * as z from "zod";

import { API_BASE } from "@/constants";
import type {
    AddMessageRequest,
    AddMessageResponse,
    ChatListResponse,
    ChatResponseItem,
    ChatMessageListResponse,
    FolderCreateRequest,
    FolderResponseItem,
    FolderUpdateRequest,
    ShareRequest,
    ShareResponseItem,
    UserSearchResponseItem,
} from "@/stores/stateful-chat/schemas";
import {
    addMessageResponseSchema,
    chatListResponseSchema,
    chatMessageListResponseSchema,
    chatResponseItemSchema,
    folderResponseItemSchema,
    shareResponseItemSchema,
    userSearchResponseItemSchema,
} from "@/stores/stateful-chat/schemas";

function authHeaders(token: string | undefined): Record<string, string> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
}

async function fetchJson<T>(
    url: string,
    options: RequestInit,
    token?: string
): Promise<T> {
    const res = await fetch(url, {
        ...options,
        headers: { ...authHeaders(token), ...options.headers } as HeadersInit,
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error (${res.status}): ${text || res.statusText}`);
    }
    if (res.status === 204) {
        return undefined as T;
    }
    return res.json() as Promise<T>;
}

export async function createChat(
    folderId: string | null | undefined,
    title: string | null | undefined,
    token?: string
): Promise<ChatResponseItem> {
    const body = { folder_id: folderId ?? null, title: title ?? null };
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats`,
        { method: "POST", body: JSON.stringify(body) },
        token
    );
    return chatResponseItemSchema.parse(json);
}

export interface ListChatsParams {
    folder_id?: string | null;
    limit?: number;
    cursor?: string | null;
}

export async function listChats(
    params: ListChatsParams,
    token?: string
): Promise<ChatListResponse> {
    const search = new URLSearchParams();
    if (params.folder_id != null) search.set("folder_id", params.folder_id);
    if (params.limit != null) search.set("limit", String(params.limit));
    if (params.cursor != null) search.set("cursor", params.cursor);
    const qs = search.toString();
    const url = `${API_BASE}/api/v1/chats${qs ? `?${qs}` : ""}`;
    const json = await fetchJson<unknown>(url, { method: "GET" }, token);
    return chatListResponseSchema.parse(json);
}

export interface ListChatsSharedWithMeParams {
    limit?: number;
    cursor?: string | null;
}

export async function listChatsSharedWithMe(
    params: ListChatsSharedWithMeParams,
    token?: string
): Promise<ChatListResponse> {
    const search = new URLSearchParams();
    if (params.limit != null) search.set("limit", String(params.limit));
    if (params.cursor != null) search.set("cursor", params.cursor);
    const qs = search.toString();
    const url = `${API_BASE}/api/v1/chats/shared-with-me${qs ? `?${qs}` : ""}`;
    const json = await fetchJson<unknown>(url, { method: "GET" }, token);
    return chatListResponseSchema.parse(json);
}

export async function getChat(
    chatId: string,
    token?: string
): Promise<ChatResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}`,
        { method: "GET" },
        token
    );
    return chatResponseItemSchema.parse(json);
}

export async function updateChat(
    chatId: string,
    body: { title?: string; folder_id?: string | null },
    token?: string
): Promise<ChatResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}`,
        { method: "PATCH", body: JSON.stringify(body) },
        token
    );
    return chatResponseItemSchema.parse(json);
}

export async function deleteChat(
    chatId: string,
    token?: string
): Promise<void> {
    await fetchJson<void>(
        `${API_BASE}/api/v1/chats/${chatId}`,
        { method: "DELETE" },
        token
    );
}

export interface GetMessagesParams {
    limit?: number;
    cursor?: string | null;
}

export async function getMessages(
    chatId: string,
    params: GetMessagesParams,
    token?: string
): Promise<ChatMessageListResponse> {
    const search = new URLSearchParams();
    if (params.limit != null) search.set("limit", String(params.limit));
    if (params.cursor != null) search.set("cursor", params.cursor);
    const qs = search.toString();
    const url = `${API_BASE}/api/v1/chats/${chatId}/messages${qs ? `?${qs}` : ""}`;
    const json = await fetchJson<unknown>(url, { method: "GET" }, token);
    return chatMessageListResponseSchema.parse(json);
}

export async function addMessage(
    chatId: string,
    body: AddMessageRequest,
    token?: string
): Promise<AddMessageResponse> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}/messages`,
        { method: "POST", body: JSON.stringify(body) },
        token
    );
    return addMessageResponseSchema.parse(json);
}

export async function listFolders(
    parentId?: string | null,
    token?: string
): Promise<FolderResponseItem[]> {
    const search = new URLSearchParams();
    if (parentId != null) search.set("parent_id", parentId);
    const qs = search.toString();
    const url = `${API_BASE}/api/v1/folders${qs ? `?${qs}` : ""}`;
    const json = await fetchJson<unknown>(url, { method: "GET" }, token);
    const arr = z.array(folderResponseItemSchema).parse(json);
    return arr;
}

export async function getFolder(
    folderId: string,
    token?: string
): Promise<FolderResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/folders/${folderId}`,
        { method: "GET" },
        token
    );
    return folderResponseItemSchema.parse(json);
}

export async function createFolder(
    body: FolderCreateRequest,
    token?: string
): Promise<FolderResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/folders`,
        { method: "POST", body: JSON.stringify(body) },
        token
    );
    return folderResponseItemSchema.parse(json);
}

export async function updateFolder(
    folderId: string,
    body: FolderUpdateRequest,
    token?: string
): Promise<FolderResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/folders/${folderId}`,
        { method: "PATCH", body: JSON.stringify(body) },
        token
    );
    return folderResponseItemSchema.parse(json);
}

export async function moveFolderToParent(
    folderId: string,
    parentId: string | null,
    token?: string
): Promise<FolderResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/folders/${folderId}/parent`,
        { method: "PATCH", body: JSON.stringify({ parent_id: parentId }) },
        token
    );
    return folderResponseItemSchema.parse(json);
}

export async function deleteFolder(
    folderId: string,
    token?: string
): Promise<void> {
    await fetchJson<void>(
        `${API_BASE}/api/v1/folders/${folderId}`,
        { method: "DELETE" },
        token
    );
}

export async function moveChatToFolder(
    chatId: string,
    folderId: string | null,
    token?: string
): Promise<ChatResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}/folder`,
        { method: "PATCH", body: JSON.stringify({ folder_id: folderId }) },
        token
    );
    return chatResponseItemSchema.parse(json);
}

export async function listShares(
    chatId: string,
    token?: string
): Promise<ShareResponseItem[]> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}/shares`,
        { method: "GET" },
        token
    );
    return z.array(shareResponseItemSchema).parse(json);
}

export async function addShare(
    chatId: string,
    body: ShareRequest,
    token?: string
): Promise<ShareResponseItem> {
    const json = await fetchJson<unknown>(
        `${API_BASE}/api/v1/chats/${chatId}/shares`,
        { method: "POST", body: JSON.stringify(body) },
        token
    );
    return shareResponseItemSchema.parse(json);
}

export async function removeShare(
    chatId: string,
    subjectType: string,
    subjectId: string,
    token?: string
): Promise<void> {
    await fetchJson<void>(
        `${API_BASE}/api/v1/chats/${chatId}/shares/${subjectType}/${subjectId}`,
        { method: "DELETE" },
        token
    );
}

export async function searchUsers(
    q: string,
    limit?: number,
    token?: string
): Promise<UserSearchResponseItem[]> {
    const search = new URLSearchParams({ q });
    if (limit != null) search.set("limit", String(limit));
    const url = `${API_BASE}/api/v1/users/search?${search.toString()}`;
    const json = await fetchJson<unknown>(url, { method: "GET" }, token);
    return z.array(userSearchResponseItemSchema).parse(json);
}
