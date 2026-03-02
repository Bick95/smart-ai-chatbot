"use client";

import { useCallback, useState } from "react";

import { sendChatMessages } from "@/api/stateless_chat";
import { ChatUI } from "@/components/chat";
import type { ChatApiMessage } from "@/stores/chat/schemas";
import { useAuthStore } from "@/stores/auth";
import { useChatStore } from "@/stores/chat";

export function ChatPage() {
    const [error, setError] = useState<{ message: string } | null>(null);
    const [isRetrying, setIsRetrying] = useState(false);
    const authToken = useAuthStore((s) => s.authToken);

    const onSendMessage = useCallback(async (content: string) => {
        setError(null);
        const store = useChatStore.getState();
        store.addMessageToCurrent({ role: "user", content });
        const chat = store.getCurrentChat();
        const chatId = store.currentChatId;
        if (!chatId || !chat) return;

        const apiMessages: ChatApiMessage[] = chat.messages.map((m) => ({
            role: m.role,
            content: m.content,
        }));

        try {
            const reply: string = await sendChatMessages(apiMessages, authToken ?? undefined);
            store.addMessage(chatId, {
                role: "assistant",
                content: reply,
            });
        } catch (err) {
            setError({
                message: err instanceof Error ? err.message : String(err),
            });
        }
    }, [authToken]);

    const onRetry = useCallback(async () => {
        setIsRetrying(true);
        setError(null);
        const store = useChatStore.getState();
        const chat = store.getCurrentChat();
        const chatId = store.currentChatId;
        if (!chatId || !chat) {
            setIsRetrying(false);
            return;
        }

        const apiMessages: ChatApiMessage[] = chat.messages.map((m) => ({
            role: m.role,
            content: m.content,
        }));

        try {
            const reply: string = await sendChatMessages(apiMessages, authToken ?? undefined);
            store.addMessage(chatId, {
                role: "assistant",
                content: reply,
            });
        } catch (err) {
            setError({
                message: err instanceof Error ? err.message : String(err),
            });
        } finally {
            setIsRetrying(false);
        }
    }, [authToken]);

    return (
        <ChatUI
            onSendMessage={onSendMessage}
            error={error}
            onRetry={onRetry}
            isRetrying={isRetrying}
        />
    );
}
