"use client";

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { ChatUI } from "@/components/chat";
import type { Message } from "@/stores/chat";
import { useAuthStore } from "@/stores/auth";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import type { ChatMessageResponseItem } from "@/stores/stateful-chat/schemas";
import { ResourceManagement } from "@/components/resource-management/ResourceManagement";
import { Button } from "@/components/ui/button";
import { Settings2 } from "lucide-react";

function mapToMessage(m: ChatMessageResponseItem): Message {
    return {
        id: m.id,
        role: m.role === "system" ? "assistant" : m.role,
        content: m.content,
        createdAt: new Date(m.created_at),
    };
}

function isOwner(ownerSubject: string): boolean {
    const user = useAuthStore.getState().user;
    if (!user) return false;
    return ownerSubject === `user:${user.id}`;
}

export function StatefulChatPage() {
    const { chatId } = useParams<{ chatId: string }>();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const isNewChat = searchParams.get("new") === "1";
    const folderIdParam = searchParams.get("folderId");

    const store = useStatefulChatStore();
    const chat = chatId ? store.chats[chatId] : null;
    const messagesData = chatId ? store.messagesByChatId[chatId] : null;
    const messages: Message[] = (messagesData?.items ?? [])
        .filter((m) => m.role !== "system")
        .map(mapToMessage);
    const hasOlderMessages = !!messagesData?.nextCursor;

    useEffect(() => {
        store.loadChats(null);
        store.loadFolders(null);
    }, [store]);

    useEffect(() => {
        if (chatId && !isNewChat) {
            store.selectChat(chatId);
            store.loadMessages(chatId);
        } else {
            store.selectChat(null);
        }
    }, [chatId, isNewChat, store]);

    const handleLoadOlder = useCallback(() => {
        if (chatId && messagesData?.nextCursor) {
            store.loadMessages(chatId, messagesData.nextCursor);
        }
    }, [chatId, messagesData?.nextCursor, store]);

    const handleSendMessage = useCallback(
        async (content: string) => {
            if (!content.trim()) return;

            if (isNewChat || !chatId) {
                const folderId = folderIdParam || undefined;
                const newChat = await store.createChat(folderId ?? null, null);
                await store.addMessage(newChat.id, content, true);
                navigate(`/chats/${newChat.id}`, { replace: true });
                return;
            }

            await store.addMessage(chatId, content, true);
        },
        [chatId, isNewChat, folderIdParam, store]
    );

    const [manageOpen, setManageOpen] = useState(false);
    const showEmptyState = !chatId && !isNewChat;

    if (showEmptyState) {
        return (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
                <h2 className="text-2xl font-semibold">Chats</h2>
                <p className="text-muted-foreground max-w-md text-sm">
                    Create a chat or select one from the list to get started.
                </p>
            </div>
        );
    }

    return (
        <div className="flex min-h-0 flex-1 flex-col">
            {chat && (
                <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border px-4 py-2">
                    <h1 className="truncate text-lg font-medium">
                        {chat.title || "Untitled chat"}
                    </h1>
                    {isOwner(chat.owner_subject) && (
                        <>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setManageOpen(true)}
                            >
                                <Settings2 className="mr-2 size-4" />
                                Manage
                            </Button>
                            <ResourceManagement
                                resourceType="chat"
                                resourceId={chat.id}
                                resourceName={chat.title ?? undefined}
                                variant="popup"
                                defaultTab="permissions"
                                open={manageOpen}
                                onClose={() => setManageOpen(false)}
                                onUpdated={() => setManageOpen(false)}
                            />
                        </>
                    )}
                </div>
            )}
            <ChatUI
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={store.isLoading}
                error={store.error ? { message: store.error } : null}
                onRetry={store.clearError}
                isRetrying={false}
                onLoadOlder={handleLoadOlder}
                hasOlderMessages={hasOlderMessages}
            />
        </div>
    );
}
