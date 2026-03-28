"use client";

import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

import { ChatUI } from "@/components/chat";
import { useStatefulChatStore } from "@/stores/stateful-chat";

export interface StatefulNewChatComposerProps {
    /** When set, new chats are created in this folder. */
    folderId?: string | null;
    /** Layout: "full" for main view, "inline" for embedding above a list. */
    variant?: "full" | "inline";
    /** Placeholder for the input. */
    placeholder?: string;
}

export function StatefulNewChatComposer({
    folderId = null,
    variant = "full",
    placeholder = "Message Chatbot...",
}: StatefulNewChatComposerProps) {
    const navigate = useNavigate();
    const store = useStatefulChatStore();

    const handleSendMessage = useCallback(
        async (content: string) => {
            if (!content.trim()) return;
            const newChat = await store.createChat(folderId ?? null, null);
            await store.addMessage(newChat.id, content, true);
            navigate(`/chats/${newChat.id}`, { replace: true });
        },
        [folderId, store, navigate]
    );

    const emptyStateSubtext = folderId
        ? "Send a message to start a new chat in this folder."
        : "Send a message to start a new chat.";

    return (
        <ChatUI
            messages={[]}
            onSendMessage={handleSendMessage}
            isLoading={store.isLoading}
            error={store.error ? { message: store.error } : null}
            onRetry={store.clearError}
            variant={variant}
            placeholder={placeholder}
            emptyStateSubtext={emptyStateSubtext}
        />
    );
}
