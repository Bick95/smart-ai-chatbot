"use client"

import { useCallback, useEffect, useRef } from "react"

import { ScrollArea } from "@/components/ui/scroll-area"
import { ItemGroup } from "@/components/ui/item"
import { useChatStore } from "@/stores/chat"
import { ChatError } from "./ChatError"
import { ChatInput } from "./ChatInput"
import { ChatMessage } from "./ChatMessage"

export interface ChatUIProps {
    /**
     * Called with the latest user message content.
     * Responsible for adding the user message, fetching the assistant reply, and adding it to the store.
     */
    onSendMessage?: (latestUserMessage: string) => Promise<void>
    /** Error to show inline (not in message history). */
    error?: { message: string } | null
    /** Called when user clicks Resubmit on the error. */
    onRetry?: () => void
    /** True while a retry is in progress. */
    isRetrying?: boolean
}

export function ChatUI({
    onSendMessage,
    error,
    onRetry,
    isRetrying = false,
}: ChatUIProps) {
    const viewportRef = useRef<HTMLDivElement>(null)
    const createChat = useChatStore((s) => s.createChat)
    const setLoading = useChatStore((s) => s.setLoading)
    const getCurrentChat = useChatStore((s) => s.getCurrentChat)
    const isLoading = useChatStore((s) => s.isLoading)

    const currentChat = getCurrentChat()
    const messages = currentChat?.messages ?? []

    // Ensure we always have a current chat for single-chat UI
    useEffect(() => {
        if (!currentChat) {
            createChat(true)
        }
    }, [currentChat, createChat])

    useEffect(() => {
        const viewport = viewportRef.current
        if (!viewport) return
        viewport.scrollTo({
            top: viewport.scrollHeight,
            behavior: "smooth",
        })
    }, [messages, isLoading, error])

    const handleSubmit = useCallback(
        async (content: string) => {
            setLoading(true)
            try {
                if (onSendMessage) {
                    await onSendMessage(content)
                }
            } finally {
                setLoading(false)
            }
        },
        [onSendMessage, setLoading]
    )

    return (
        <div className="flex h-dvh flex-col bg-background">
            <main className="flex flex-1 flex-col overflow-hidden">
                <ScrollArea className="min-h-0 flex-1" viewportRef={viewportRef}>
                    <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-6">
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
    )
}
