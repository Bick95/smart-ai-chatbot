"use client";

import { useCallback, useState } from "react";

import { sendChatMessages } from "@/api/stateless_chat";
import { ChatUI } from "@/components/chat";
import type { ChatApiMessage } from "@/stores/chat/schemas";
import { useAuthStore } from "@/stores/auth";
import { useChatStore } from "@/stores/chat";
import { formatCaughtError } from "@/lib/format-errors";

export function ChatPage() {
    const [error, setError] = useState<{ message: string } | null>(null);
    const [isRetrying, setIsRetrying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const authToken = useAuthStore((s) => s.authToken);

    const getCurrentChat = useChatStore((s) => s.getCurrentChat);
    const createChat = useChatStore((s) => s.createChat);
    const currentChat = getCurrentChat();
    const messages = currentChat?.messages ?? [];

    const sendAndFetchReply = useCallback(
        async (userContent?: string) => {
            setError(null);
            setIsLoading(true);
            const store = useChatStore.getState();

            if (userContent !== undefined) {
                store.addMessageToCurrent({ role: "user", content: userContent });
            }

            const chat = store.getCurrentChat();
            const chatId = store.currentChatId;
            if (!chatId || !chat) {
                setIsLoading(false);
                return;
            }

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
                    message: formatCaughtError(err, "Sending the message failed."),
                });
            } finally {
                setIsLoading(false);
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

    const createChatIfNeeded = useCallback(() => {
        if (!currentChat) {
            createChat(true);
        }
    }, [currentChat, createChat]);

    return (
        <ChatUI
            messages={messages}
            onSendMessage={onSendMessage}
            isLoading={isLoading}
            error={error}
            onRetry={onRetry}
            isRetrying={isRetrying}
            createChatIfNeeded={createChatIfNeeded}
            emptyStateSubtext="Send a message to get started. Conversations are stored locally and sent to the backend for AI responses."
        />
    );
}
