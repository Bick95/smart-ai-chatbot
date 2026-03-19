import { create } from "zustand";

import type { Chat, Message, MessageInput } from "./schemas";
import { chatSchema, messageInputSchema, messageSchema } from "./schemas";

function generateId(): string {
    return (
        crypto.randomUUID?.() ??
        `id-${Date.now()}-${Math.random().toString(36).slice(2)}`
    );
}

interface ChatState {
    /** All chats keyed by ID */
    chats: Record<string, Chat>;
    /** Currently selected chat ID */
    currentChatId: string | null;
    /** Whether an assistant response is being generated */
    isLoading: boolean;
}

interface ChatActions {
    /** Create a new chat and optionally select it */
    createChat: (select?: boolean) => string;
    /** Select a chat by ID */
    selectChat: (id: string | null) => void;
    /** Add a message to a specific chat (validates with Zod) */
    addMessage: (chatId: string, input: MessageInput) => Message;
    /** Add a message to the current chat (no-op if none selected) */
    addMessageToCurrent: (input: MessageInput) => Message | null;
    /** Set loading state */
    setLoading: (loading: boolean) => void;
    /** Get the current chat */
    getCurrentChat: () => Chat | null;
    /** Get messages for a chat */
    getMessages: (chatId: string) => Message[];
    /** Reset temporary chat: clear all chats and selection */
    resetTemporaryChat: () => void;
}

const initialState: ChatState = {
    chats: {},
    currentChatId: null,
    isLoading: false,
};

export const useChatStore = create<ChatState & ChatActions>((set, get) => ({
    ...initialState,

    createChat: (select = true) => {
        const { currentChatId } = get();
        const id = generateId();
        const chat: Chat = {
            id,
            messages: [],
            createdAt: new Date(),
            updatedAt: new Date(),
        };
        const parsed = chatSchema.parse(chat);
        set((state) => ({
            chats: { ...state.chats, [id]: parsed },
            currentChatId: select || !currentChatId ? id : state.currentChatId,
        }));
        return id;
    },

    selectChat: (id) => {
        set({ currentChatId: id });
    },

    addMessage: (chatId, input) => {
        const parsed = messageInputSchema.parse(input);
        const message: Message = {
            id: generateId(),
            role: parsed.role,
            content: parsed.content,
            createdAt: new Date(),
        };
        const validated = messageSchema.parse(message);

        set((state) => {
            const chat = state.chats[chatId];
            if (!chat) return state;
            return {
                chats: {
                    ...state.chats,
                    [chatId]: {
                        ...chat,
                        messages: [...chat.messages, validated],
                        updatedAt: new Date(),
                    },
                },
            };
        });
        return validated;
    },

    addMessageToCurrent: (input) => {
        const { currentChatId } = get();
        if (!currentChatId) return null;
        return get().addMessage(currentChatId, input);
    },

    setLoading: (loading) => set({ isLoading: loading }),

    getCurrentChat: () => {
        const { currentChatId, chats } = get();
        if (!currentChatId) return null;
        return chats[currentChatId] ?? null;
    },

    getMessages: (chatId) => {
        const chat = get().chats[chatId];
        return chat?.messages ?? [];
    },

    resetTemporaryChat: () => {
        set({ chats: {}, currentChatId: null });
    },
}));
