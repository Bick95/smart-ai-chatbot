import type { AnchorHTMLAttributes } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  Item,
  ItemContent,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item"
import { cn } from "@/lib/utils"
import type { Message } from "@/stores/chat"
import { Bot, User } from "lucide-react"

function SafeLink({
  href,
  children,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement>) {
  const url = String(href ?? "")
  const isSafe =
    url.startsWith("http://") ||
    url.startsWith("https://") ||
    url.startsWith("mailto:")

  if (!isSafe) return <span>{children}</span>

  return (
    <a href={url} target="_blank" rel="noopener noreferrer nofollow" {...props}>
      {children}
    </a>
  )
}

export interface ChatMessageProps {
  message: Message
  className?: string
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const isUser = message.role === "user"

  return (
    <Item
      variant={isUser ? "default" : "muted"}
      size="default"
      className={cn(
        "w-fit max-w-[95%] rounded-2xl",
        isUser
          ? "ml-auto flex-row-reverse border border-border bg-muted/80 text-foreground"
          : "mr-auto flex-row bg-muted text-foreground",
        className
      )}
    >
      <ItemMedia variant="icon">
        {isUser ? (
          <User className="size-4" aria-hidden />
        ) : (
          <Bot className="size-4" aria-hidden />
        )}
      </ItemMedia>
      <ItemContent className={cn("min-w-0 flex-1", isUser && "text-right")}>
        <ItemTitle className="text-xs font-medium opacity-80">
          {isUser ? "You" : "Assistant"}
        </ItemTitle>
        <div className="markdown-content mt-1 max-w-none break-words text-sm font-normal">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: SafeLink,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </ItemContent>
    </Item>
  )
}
