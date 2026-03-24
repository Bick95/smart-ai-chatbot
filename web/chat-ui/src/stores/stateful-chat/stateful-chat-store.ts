import { create } from "zustand";

import * as api from "@/api/stateful_chat";
import { useAuthStore } from "@/stores/auth";
import type {
    ChatMessageResponseItem,
    ChatResponseItem,
    FolderResponseItem,
    ShareResponseItem,
} from "./schemas";

interface StatefulChatState {
    chats: Record<string, ChatResponseItem>;
    currentChatId: string | null;
    folders: FolderResponseItem[];
    foldersByParent: Record<string | "root", FolderResponseItem[]>;
    currentFolder: FolderResponseItem | null;
    recentChats: ChatResponseItem[];
    recentChatsNextCursor: string | null;
    /** Chats shared with the current user (flat list; not grouped by owner's folders). */
    sharedWithMeChats: ChatResponseItem[];
    sharedWithMeNextCursor: string | null;
    messagesByChatId: Record<string, { items: ChatMessageResponseItem[]; nextCursor: string | null }>;
    folderChatsByFolderId: Record<string, { items: ChatResponseItem[]; nextCursor: string | null }>;
    sharesByChatId: Record<string, ShareResponseItem[]>;
    expandedFolderIds: Set<string>;
    isLoading: boolean;
    error: string | null;
}

interface StatefulChatActions {
    createChat: (folderId?: string | null, title?: string | null) => Promise<ChatResponseItem>;
    selectChat: (id: string | null) => void;
    loadChats: (folderId?: string | null, cursor?: string | null) => Promise<void>;
    loadSharedWithMeChats: (cursor?: string | null) => Promise<void>;
    loadFolders: (parentId?: string | null) => Promise<FolderResponseItem[]>;
    loadFolder: (folderId: string) => Promise<FolderResponseItem | null>;
    loadMessages: (chatId: string, cursor?: string | null) => Promise<void>;
    addMessage: (chatId: string, content: string, generateReply?: boolean) => Promise<string | null>;
    updateChat: (chatId: string, updates: { title?: string; folder_id?: string | null }) => Promise<ChatResponseItem | null>;
    deleteChat: (chatId: string) => Promise<boolean>;
    moveChatToFolder: (chatId: string, folderId: string | null) => Promise<boolean>;
    createFolder: (name: string, parentId?: string | null, systemPrompt?: string | null) => Promise<FolderResponseItem>;
    renameFolder: (folderId: string, name: string) => Promise<FolderResponseItem | null>;
    updateFolder: (folderId: string, updates: { name?: string; system_prompt?: string | null }) => Promise<FolderResponseItem | null>;
    deleteFolder: (folderId: string) => Promise<boolean>;
    moveFolderToParent: (folderId: string, parentId: string | null) => Promise<FolderResponseItem | null>;
    loadShares: (chatId: string) => Promise<ShareResponseItem[]>;
    addShare: (chatId: string, subjectType: string, subjectId: string, role: "viewer" | "editor") => Promise<ShareResponseItem>;
    removeShare: (chatId: string, subjectType: string, subjectId: string) => Promise<boolean>;
    toggleExpandedFolder: (folderId: string) => void;
    ensureFolderExpanded: (folderId: string) => void;
    setError: (error: string | null) => void;
    clearError: () => void;
    /** Clear all user data. Call on logout or when user changes. */
    reset: () => void;
}

const EXPANDED_FOLDERS_KEY = "chats-sidebar-expanded-folders";

function loadExpandedFolderIds(): Set<string> {
    if (typeof sessionStorage === "undefined") return new Set();
    try {
        const saved = sessionStorage.getItem(EXPANDED_FOLDERS_KEY);
        if (saved) {
            const ids = JSON.parse(saved) as unknown;
            return new Set(Array.isArray(ids) ? ids : []);
        }
    } catch {
        // ignore
    }
    return new Set();
}

function saveExpandedFolderIds(ids: Set<string>): void {
    if (typeof sessionStorage === "undefined") return;
    try {
        sessionStorage.setItem(
            EXPANDED_FOLDERS_KEY,
            JSON.stringify([...ids])
        );
    } catch {
        // ignore
    }
}

function getToken(): string | undefined {
    return useAuthStore.getState().authToken ?? undefined;
}

export const useStatefulChatStore = create<
    StatefulChatState & StatefulChatActions
>((set, get) => ({
    chats: {},
    currentChatId: null,
    folders: [],
    foldersByParent: {},
    currentFolder: null,
    recentChats: [],
    recentChatsNextCursor: null,
    sharedWithMeChats: [],
    sharedWithMeNextCursor: null,
    messagesByChatId: {},
    folderChatsByFolderId: {},
    sharesByChatId: {},
    expandedFolderIds: loadExpandedFolderIds(),
    isLoading: false,
    error: null,

    toggleExpandedFolder: (folderId) =>
        set((s) => {
            const next = new Set(s.expandedFolderIds);
            if (next.has(folderId)) next.delete(folderId);
            else next.add(folderId);
            saveExpandedFolderIds(next);
            return { expandedFolderIds: next };
        }),

    ensureFolderExpanded: (folderId) =>
        set((s) => {
            if (s.expandedFolderIds.has(folderId)) return s;
            const allFolders = Object.values(s.foldersByParent).flat();
            const byId = new Map(allFolders.map((f) => [f.id, f]));
            if (s.currentFolder?.id === folderId) byId.set(folderId, s.currentFolder);
            const toExpand = new Set<string>();
            let current: FolderResponseItem | undefined = byId.get(folderId);
            while (current) {
                toExpand.add(current.id);
                const parentId = current.parent_id ?? null;
                if (!parentId) break;
                current = byId.get(parentId);
            }
            if (toExpand.size === 0) return s;
            const next = new Set(s.expandedFolderIds);
            for (const id of toExpand) next.add(id);
            saveExpandedFolderIds(next);
            return { expandedFolderIds: next };
        }),

    createChat: async (folderId, title) => {
        set({ isLoading: true, error: null });
        try {
            const chat = await api.createChat(folderId, title, getToken());
            set((s) => {
                const updates: Record<string, unknown> = {
                    chats: { ...s.chats, [chat.id]: chat },
                    currentChatId: chat.id,
                    recentChats: [chat, ...s.recentChats.filter((c) => c.id !== chat.id)],
                    isLoading: false,
                };
                if (folderId) {
                    const key = folderId;
                    const existing = s.folderChatsByFolderId[key];
                    updates.folderChatsByFolderId = {
                        ...s.folderChatsByFolderId,
                        [key]: {
                            items: [chat, ...(existing?.items ?? [])],
                            nextCursor: existing?.nextCursor ?? null,
                        },
                    };
                }
                return updates;
            });
            return chat;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to create chat",
            });
            throw e;
        }
    },

    selectChat: (id) => set({ currentChatId: id }),

    loadChats: async (folderId, cursor) => {
        set({ isLoading: true, error: null });
        try {
            const res = await api.listChats(
                { folder_id: folderId ?? undefined, cursor: cursor ?? undefined, limit: 50 },
                getToken()
            );
            const byId = { ...get().chats };
            for (const c of res.items) {
                byId[c.id] = c;
            }
            set((s) => {
                if (folderId == null) {
                    return {
                        chats: byId,
                        recentChats: res.items,
                        recentChatsNextCursor: res.next_cursor ?? null,
                        isLoading: false,
                    };
                }
                const key = folderId;
                const existing = s.folderChatsByFolderId[key];
                const items = cursor
                    ? [...(existing?.items ?? []), ...res.items]
                    : res.items;
                return {
                    chats: byId,
                    folderChatsByFolderId: {
                        ...s.folderChatsByFolderId,
                        [key]: {
                            items,
                            nextCursor: res.next_cursor ?? null,
                        },
                    },
                    isLoading: false,
                };
            });
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to load chats",
            });
        }
    },

    loadSharedWithMeChats: async (cursor?: string | null) => {
        set({ isLoading: true, error: null });
        try {
            const res = await api.listChatsSharedWithMe(
                { cursor: cursor ?? undefined, limit: 50 },
                getToken()
            );
            const byId = { ...get().chats };
            for (const c of res.items) {
                byId[c.id] = c;
            }
            set((s) => ({
                chats: byId,
                sharedWithMeChats: cursor
                    ? [...s.sharedWithMeChats, ...res.items]
                    : res.items,
                sharedWithMeNextCursor: res.next_cursor ?? null,
                isLoading: false,
            }));
        } catch (e) {
            set({
                isLoading: false,
                error:
                    e instanceof Error
                        ? e.message
                        : "Failed to load shared chats",
            });
        }
    },

    loadFolders: async (parentId) => {
        set({ isLoading: true, error: null });
        try {
            const folders = await api.listFolders(parentId ?? null, getToken());
            const key = parentId ?? "root";
            set((s) => ({
                foldersByParent: { ...s.foldersByParent, [key]: folders },
                folders: [...s.folders.filter((f) => (parentId ? f.parent_id !== parentId : f.parent_id !== null)), ...folders],
                isLoading: false,
            }));
            return folders;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to load folders",
            });
            return [];
        }
    },

    loadFolder: async (folderId) => {
        set({ isLoading: true, error: null });
        try {
            const folder = await api.getFolder(folderId, getToken());
            set((s) => ({
                chats: { ...s.chats },
                currentFolder: folder,
                isLoading: false,
            }));
            return folder;
        } catch {
            set({ isLoading: false, currentFolder: null });
            return null;
        }
    },

    loadMessages: async (chatId, cursor) => {
        set({ isLoading: true, error: null });
        try {
            const res = await api.getMessages(
                chatId,
                { cursor: cursor ?? undefined, limit: 50 },
                getToken()
            );
            const existing = get().messagesByChatId[chatId]?.items ?? [];
            const merged = cursor
                ? [...existing, ...res.items]
                : res.items;
            set((s) => ({
                messagesByChatId: {
                    ...s.messagesByChatId,
                    [chatId]: {
                        items: merged,
                        nextCursor: res.next_cursor ?? null,
                    },
                },
                isLoading: false,
            }));
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to load messages",
            });
        }
    },

    addMessage: async (chatId, content, generateReply = true) => {
        set({ isLoading: true, error: null });
        try {
            const res = await api.addMessage(
                chatId,
                { role: "user", content, generate_reply: generateReply },
                getToken()
            );
            const userMsg = res.message;
            set((s) => {
                const prev = s.messagesByChatId[chatId] ?? { items: [], nextCursor: null };
                const items = [...prev.items, userMsg];
                if (res.reply) {
                    items.push({
                        id: `temp-${Date.now()}`,
                        chat_id: chatId,
                        role: "assistant",
                        content: res.reply,
                        created_at: new Date().toISOString(),
                    } as ChatMessageResponseItem & { id: string });
                }
                const chat = s.chats[chatId];
                const needsTitle =
                    chat &&
                    (!chat.title || !chat.title.trim()) &&
                    userMsg.role === "user" &&
                    content.trim();
                const newTitle = needsTitle
                    ? content.trim().slice(0, 30)
                    : undefined;
                const updatedChat =
                    newTitle && chat
                        ? { ...chat, title: newTitle }
                        : undefined;
                const folderId = chat?.folder_id ?? null;
                const folderChats =
                    updatedChat && folderId
                        ? {
                              ...s.folderChatsByFolderId,
                              [folderId]: {
                                  ...s.folderChatsByFolderId[folderId],
                                  items: (
                                      s.folderChatsByFolderId[folderId]
                                          ?.items ?? []
                                  ).map((c) =>
                                      c.id === chatId ? updatedChat : c
                                  ),
                              },
                          }
                        : s.folderChatsByFolderId;
                return {
                    messagesByChatId: {
                        ...s.messagesByChatId,
                        [chatId]: { ...prev, items },
                    },
                    chats:
                        updatedChat
                            ? { ...s.chats, [chatId]: updatedChat }
                            : s.chats,
                    recentChats:
                        updatedChat
                            ? s.recentChats.map((c) =>
                                  c.id === chatId ? updatedChat : c
                              )
                            : s.recentChats,
                    sharedWithMeChats:
                        updatedChat
                            ? s.sharedWithMeChats.map((c) =>
                                  c.id === chatId ? updatedChat : c
                              )
                            : s.sharedWithMeChats,
                    folderChatsByFolderId: folderChats,
                    isLoading: false,
                };
            });
            return res.reply ?? null;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to send message",
            });
            throw e;
        }
    },

    updateChat: async (chatId, updates) => {
        set({ isLoading: true, error: null });
        try {
            const prevChat = get().chats[chatId];
            const chat = await api.updateChat(chatId, updates, getToken());
            set((s) => {
                const oldF = prevChat?.folder_id ?? null;
                const newF = chat.folder_id ?? null;
                const folderChatsByFolderId = { ...s.folderChatsByFolderId };

                if (oldF !== newF) {
                    if (oldF) {
                        const b = folderChatsByFolderId[oldF];
                        if (b) {
                            folderChatsByFolderId[oldF] = {
                                ...b,
                                items: (b.items ?? []).filter(
                                    (c) => c.id !== chatId
                                ),
                            };
                        }
                    }
                    if (newF) {
                        const b = folderChatsByFolderId[newF];
                        const rest = (b?.items ?? []).filter(
                            (c) => c.id !== chatId
                        );
                        folderChatsByFolderId[newF] = {
                            items: [chat, ...rest],
                            nextCursor: b?.nextCursor ?? null,
                        };
                    }
                } else {
                    for (const key of Object.keys(folderChatsByFolderId)) {
                        const b = folderChatsByFolderId[key];
                        const items = b?.items ?? [];
                        if (!items.some((c) => c.id === chatId)) continue;
                        folderChatsByFolderId[key] = {
                            ...b,
                            items: items.map((c) =>
                                c.id === chatId ? chat : c
                            ),
                        };
                    }
                }

                return {
                    chats: { ...s.chats, [chat.id]: chat },
                    recentChats: s.recentChats.map((c) =>
                        c.id === chatId ? chat : c
                    ),
                    sharedWithMeChats: s.sharedWithMeChats.map((c) =>
                        c.id === chatId ? chat : c
                    ),
                    folderChatsByFolderId,
                    isLoading: false,
                };
            });
            return chat;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to update chat",
            });
            return null;
        }
    },

    deleteChat: async (chatId) => {
        set({ isLoading: true, error: null });
        try {
            const chat = get().chats[chatId];
            await api.deleteChat(chatId, getToken());
            set((s) => {
                const chats = { ...s.chats };
                delete chats[chatId];
                const msgs = { ...s.messagesByChatId };
                delete msgs[chatId];
                const folderId = chat?.folder_id ?? null;
                const folderChats = folderId
                    ? {
                          ...s.folderChatsByFolderId,
                          [folderId]: {
                              ...s.folderChatsByFolderId[folderId],
                              items: (s.folderChatsByFolderId[folderId]?.items ?? []).filter(
                                  (c) => c.id !== chatId
                              ),
                          },
                      }
                    : s.folderChatsByFolderId;
                return {
                    chats,
                    messagesByChatId: msgs,
                    folderChatsByFolderId: folderChats,
                    currentChatId: s.currentChatId === chatId ? null : s.currentChatId,
                    recentChats: s.recentChats.filter((c) => c.id !== chatId),
                    sharedWithMeChats: s.sharedWithMeChats.filter(
                        (c) => c.id !== chatId
                    ),
                    isLoading: false,
                };
            });
            return true;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to delete chat",
            });
            return false;
        }
    },

    moveChatToFolder: async (chatId, folderId) => {
        set({ isLoading: true, error: null });
        try {
            const oldChat = get().chats[chatId];
            const chat = await api.moveChatToFolder(chatId, folderId, getToken());
            set((s) => {
                const oldFolderId = oldChat?.folder_id ?? null;
                const folderChats = { ...s.folderChatsByFolderId };
                if (oldFolderId) {
                    folderChats[oldFolderId] = {
                        ...folderChats[oldFolderId],
                        items: (folderChats[oldFolderId]?.items ?? []).filter(
                            (c) => c.id !== chatId
                        ),
                    };
                }
                if (folderId) {
                    folderChats[folderId] = {
                        items: [chat, ...(folderChats[folderId]?.items ?? [])],
                        nextCursor: folderChats[folderId]?.nextCursor ?? null,
                    };
                }
                return {
                    chats: { ...s.chats, [chat.id]: chat },
                    folderChatsByFolderId: folderChats,
                    recentChats: s.recentChats.map((c) =>
                        c.id === chatId ? chat : c
                    ),
                    sharedWithMeChats: s.sharedWithMeChats.map((c) =>
                        c.id === chatId ? chat : c
                    ),
                    isLoading: false,
                };
            });
            return true;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to move chat",
            });
            return false;
        }
    },

    createFolder: async (name, parentId, systemPrompt) => {
        set({ isLoading: true, error: null });
        try {
            const folder = await api.createFolder(
                { name, parent_id: parentId ?? undefined, system_prompt: systemPrompt ?? undefined },
                getToken()
            );
            const key = parentId ?? "root";
            set((s) => ({
                foldersByParent: {
                    ...s.foldersByParent,
                    [key]: [...(s.foldersByParent[key] ?? []), folder],
                },
                isLoading: false,
            }));
            return folder;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to create folder",
            });
            throw e;
        }
    },

    renameFolder: async (folderId, name) => {
        return get().updateFolder(folderId, { name });
    },

    updateFolder: async (folderId, updates) => {
        set({ isLoading: true, error: null });
        try {
            const patch: { name?: string; system_prompt?: string | null } = {};
            if (updates.name != null) patch.name = updates.name;
            if (updates.system_prompt !== undefined) patch.system_prompt = updates.system_prompt;
            if (Object.keys(patch).length === 0) {
                return get().currentFolder?.id === folderId ? get().currentFolder : null;
            }
            const folder = await api.updateFolder(folderId, patch, getToken());
            set((s) => {
                const byParent = { ...s.foldersByParent };
                for (const key of Object.keys(byParent)) {
                    byParent[key] = byParent[key].map((f) =>
                        f.id === folderId ? folder : f
                    );
                }
                const folders =
                    s.folders.length > 0
                        ? s.folders.map((f) =>
                              f.id === folderId ? folder : f
                          )
                        : s.folders;
                return {
                    foldersByParent: byParent,
                    folders,
                    currentFolder:
                        s.currentFolder?.id === folderId
                            ? folder
                            : s.currentFolder,
                    isLoading: false,
                };
            });
            return folder;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to update folder",
            });
            return null;
        }
    },

    deleteFolder: async (folderId) => {
        set({ isLoading: true, error: null });
        try {
            await api.deleteFolder(folderId, getToken());
            set((s) => {
                const byParent = { ...s.foldersByParent };
                for (const key of Object.keys(byParent)) {
                    byParent[key] = byParent[key].filter((f) => f.id !== folderId);
                }
                return {
                    foldersByParent: byParent,
                    currentFolder: s.currentFolder?.id === folderId ? null : s.currentFolder,
                    isLoading: false,
                };
            });
            return true;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to delete folder",
            });
            return false;
        }
    },

    moveFolderToParent: async (folderId, parentId) => {
        set({ isLoading: true, error: null });
        try {
            const folder = await api.moveFolderToParent(
                folderId,
                parentId,
                getToken()
            );
            set((s) => {
                const byParent = { ...s.foldersByParent };
                const oldKey = s.currentFolder?.id === folderId ? (s.currentFolder.parent_id ?? "root") : "root";
                const newKey = parentId ?? "root";
                if (byParent[oldKey]) {
                    byParent[oldKey] = byParent[oldKey].filter((f) => f.id !== folderId);
                }
                byParent[newKey] = [...(byParent[newKey] ?? []), folder];
                return {
                    foldersByParent: byParent,
                    currentFolder: s.currentFolder?.id === folderId ? folder : s.currentFolder,
                    isLoading: false,
                };
            });
            return folder;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to move folder",
            });
            return null;
        }
    },

    loadShares: async (chatId) => {
        set({ isLoading: true, error: null });
        try {
            const shares = await api.listShares(chatId, getToken());
            set((s) => ({
                sharesByChatId: { ...s.sharesByChatId, [chatId]: shares },
                isLoading: false,
            }));
            return shares;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to load shares",
            });
            return [];
        }
    },

    addShare: async (chatId, subjectType, subjectId, role) => {
        set({ isLoading: true, error: null });
        try {
            const share = await api.addShare(
                chatId,
                { subject_type: subjectType as "user" | "service_account" | "group", subject_id: subjectId, role },
                getToken()
            );
            set((s) => ({
                sharesByChatId: {
                    ...s.sharesByChatId,
                    [chatId]: [...(s.sharesByChatId[chatId] ?? []), share],
                },
                isLoading: false,
            }));
            return share;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to add share",
            });
            throw e;
        }
    },

    removeShare: async (chatId, subjectType, subjectId) => {
        set({ isLoading: true, error: null });
        try {
            await api.removeShare(chatId, subjectType, subjectId, getToken());
            set((s) => ({
                sharesByChatId: {
                    ...s.sharesByChatId,
                    [chatId]: (s.sharesByChatId[chatId] ?? []).filter(
                        (sh) => !(sh.subject === `${subjectType}:${subjectId}`)
                    ),
                },
                isLoading: false,
            }));
            return true;
        } catch (e) {
            set({
                isLoading: false,
                error: e instanceof Error ? e.message : "Failed to remove share",
            });
            return false;
        }
    },

    setError: (error) => set({ error }),
    clearError: () => set({ error: null }),

    reset: () => {
        set({
            chats: {},
            currentChatId: null,
            folders: [],
            foldersByParent: {},
            currentFolder: null,
            recentChats: [],
            recentChatsNextCursor: null,
            sharedWithMeChats: [],
            sharedWithMeNextCursor: null,
            messagesByChatId: {},
            folderChatsByFolderId: {},
            sharesByChatId: {},
            isLoading: false,
            error: null,
        });
        if (typeof sessionStorage !== "undefined") {
            try {
                sessionStorage.removeItem(EXPANDED_FOLDERS_KEY);
            } catch {
                // ignore
            }
        }
        set({ expandedFolderIds: new Set() });
    },
}));
