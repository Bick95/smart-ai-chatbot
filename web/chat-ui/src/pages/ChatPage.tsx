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

    const sendAndFetchReply = useCallback(
        async (userContent?: string) => {
            setError(null);
            const store = useChatStore.getState();

            if (userContent !== undefined) {
                store.addMessageToCurrent({ role: "user", content: userContent });
            }

            const chat = store.getCurrentChat();
            const chatId = store.currentChatId;
            if (!chatId || !chat) return;

            const apiMessages: ChatApiMessage[] = chat.messages.map((m) => ({
                role: m.role,
                content: m.content,
            }));

            try {
                const reply = await sendChatMessages(
                    apiMessages,
                    authToken ?? undefined
                );
                store.addMessage(chatId, {
                    role: "assistant",
                    content: reply,
                });
            } catch (err) {
                setError({
                    message: err instanceof Error ? err.message : String(err),
                });
            }
        },
        [authToken]
    );

    const onSendMessage = useCallback(
        (content: string): Promise<void> => {
            if (!content.trim()) return Promise.resolve();
            return sendAndFetchReply(content);
        },
        [sendAndFetchReply]
    );

    const onRetry = useCallback(async () => {
        setIsRetrying(true);
        try {
            await sendAndFetchReply();
        } finally {
            setIsRetrying(false);
        }
    }, [sendAndFetchReply]);

    return (
        <ChatUI
            onSendMessage={onSendMessage}
            error={error}
            onRetry={onRetry}
            isRetrying={isRetrying}
        />
    );
}
