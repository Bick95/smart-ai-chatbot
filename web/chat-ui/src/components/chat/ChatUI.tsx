"use client";

import { useCallback, useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { ItemGroup } from "@/components/ui/item";
import type { Message } from "@/stores/chat";
import { ChatError } from "./ChatError";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";

export interface ChatUIProps {
    /** Messages to display (user + assistant). */
    messages: Message[];
    /**
     * Called with the latest user message content.
     * Responsible for adding the user message, fetching the assistant reply, and adding it.
     */
    onSendMessage: (latestUserMessage: string) => Promise<void>;
    /** Whether an assistant response is being generated. */
    isLoading?: boolean;
    /** Error to show inline (not in message history). */
    error?: { message: string } | null;
    /** Called when user clicks Resubmit on the error. */
    onRetry?: () => void;
    /** True while a retry is in progress. */
    isRetrying?: boolean;
    /** Called on mount if no messages; use to ensure a chat exists (e.g. temporary chat). */
    createChatIfNeeded?: () => void;
    /** If provided and has cursor, shows "Load older" at top for pagination. */
    onLoadOlder?: () => void;
    /** Cursor for loading older messages; when set, onLoadOlder can fetch more. */
    hasOlderMessages?: boolean;
}

export function ChatUI({
    messages,
    onSendMessage,
    isLoading = false,
    error,
    onRetry,
    isRetrying = false,
    createChatIfNeeded,
    onLoadOlder,
    hasOlderMessages,
}: ChatUIProps) {
    const viewportRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (createChatIfNeeded && messages.length === 0 && !isLoading && !error) {
            createChatIfNeeded();
        }
    }, [createChatIfNeeded, messages.length, isLoading, error]);

    // Scroll to bottom whenever content at the bottom changes: new messages,
    // loading indicator appears/disappears, or error state.
    useEffect(() => {
        const viewport = viewportRef.current;
        if (!viewport) return;
        viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: "smooth",
        });
    }, [messages, isLoading, error]);

    const handleSubmit = useCallback(
        async (content: string) => {
            if (!content.trim()) return;
            await onSendMessage(content);
        },
        [onSendMessage],
    );

    return (
        <div className="flex min-h-0 flex-1 flex-col bg-background">
            <main className="flex flex-1 flex-col overflow-hidden">
                <ScrollArea
                    className="min-h-0 flex-1"
                    viewportRef={viewportRef}
                >
                    <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-6">
                        {hasOlderMessages && onLoadOlder && (
                            <div className="flex justify-center py-2">
                                <button
                                    type="button"
                                    className="text-muted-foreground hover:text-foreground text-sm underline"
                                    onClick={onLoadOlder}
                                >
                                    Load older messages
                                </button>
                            </div>
                        )}
                        {messages.length === 0 && !isLoading && !error ? (
                            <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                                <h2 className="text-2xl font-semibold">
                                    How can I help you today?
                                </h2>
                                <p className="text-muted-foreground max-w-md text-sm">
                                    Send a message to get started. Conversations
                                    are stored locally and sent to the backend
                                    for AI responses.
                                </p>
                            </div>
                        ) : (
                            <ItemGroup className="gap-2">
                                {messages.map((msg) => (
                                    <ChatMessage key={msg.id} message={msg} />
                                ))}
                                {error && onRetry && (
                                    <ChatError
                                        message={error.message}
                                        onRetry={onRetry}
                                        isRetrying={isRetrying}
                                    />
                                )}
                                {isLoading && (
                                    <div className="bg-muted flex w-full max-w-[95%] items-center gap-2 self-start rounded-2xl px-4 py-3">
                                        <span
                                            className="bg-muted-foreground size-2 animate-pulse rounded-full"
                                            style={{ animationDelay: "0ms" }}
                                        />
                                        <span
                                            className="bg-muted-foreground size-2 animate-pulse rounded-full"
                                            style={{ animationDelay: "150ms" }}
                                        />
                                        <span
                                            className="bg-muted-foreground size-2 animate-pulse rounded-full"
                                            style={{ animationDelay: "300ms" }}
                                        />
                                    </div>
                                )}
                            </ItemGroup>
                        )}
                    </div>
                </ScrollArea>

                <div className="shrink-0 border-t border-border bg-background">
                    <div className="mx-auto max-w-3xl px-4 py-4">
                        <ChatInput
                            onSubmit={handleSubmit}
                            disabled={isLoading || isRetrying}
                            placeholder="Message ChatGPT..."
                        />
                    </div>
                </div>
            </main>
        </div>
    );
}
