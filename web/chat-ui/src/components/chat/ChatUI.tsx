"use client"

import * as React from "react"

import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ItemGroup,
} from "@/components/ui/item"
import { useChatStore } from "@/stores/chat"
import { ChatInput } from "./ChatInput"
import { ChatMessage } from "./ChatMessage"

export interface ChatUIProps {
  /** Optional: provide a function to generate assistant responses. If not provided, uses a demo echo. */
  onSendMessage?: (message: string) => Promise<string>
}

export function ChatUI({ onSendMessage }: ChatUIProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const createChat = useChatStore((s) => s.createChat)
  const addMessageToCurrent = useChatStore((s) => s.addMessageToCurrent)
  const setLoading = useChatStore((s) => s.setLoading)
  const getCurrentChat = useChatStore((s) => s.getCurrentChat)
  const isLoading = useChatStore((s) => s.isLoading)

  const currentChat = getCurrentChat()
  const messages = currentChat?.messages ?? []

  // Ensure we always have a current chat for single-chat UI
  React.useEffect(() => {
    if (!currentChat) {
      createChat(true)
    }
  }, [currentChat, createChat])

  React.useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const handleSubmit = React.useCallback(
    async (content: string) => {
      addMessageToCurrent({ role: "user", content })
      setLoading(true)

      try {
        const assistantContent = onSendMessage
          ? await onSendMessage(content)
          : await new Promise<string>((resolve) => {
              setTimeout(
                () => resolve(`This is a demo response to: "${content}"`),
                600
              )
            })

        const chatId = useChatStore.getState().currentChatId
        if (chatId) {
          useChatStore.getState().addMessage(chatId, {
            role: "assistant",
            content: assistantContent,
          })
        }
      } finally {
        setLoading(false)
      }
    },
    [addMessageToCurrent, onSendMessage, setLoading]
  )

  return (
    <div className="flex h-dvh flex-col bg-background">
      <main className="flex flex-1 flex-col overflow-hidden">
        <ScrollArea className="flex-1">
          <div className="mx-auto flex max-w-3xl flex-col gap-2 px-4 py-6">
            {messages.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                <h2 className="text-2xl font-semibold">How can I help you today?</h2>
                <p className="text-muted-foreground max-w-md text-sm">
                  Send a message to get started. This is a demo chat — responses
                  are simulated.
                </p>
              </div>
            ) : (
              <ItemGroup className="gap-2">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
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
                <div ref={scrollRef} aria-hidden />
              </ItemGroup>
            )}
          </div>
        </ScrollArea>

        <div className="border-t border-border bg-background">
          <div className="mx-auto max-w-3xl px-4 py-4">
            <ChatInput
              onSubmit={handleSubmit}
              disabled={isLoading}
              placeholder="Message ChatGPT..."
            />
          </div>
        </div>
      </main>
    </div>
  )
}
