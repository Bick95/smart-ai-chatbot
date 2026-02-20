import {
  Item,
  ItemContent,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item"
import { cn } from "@/lib/utils"
import type { Message } from "@/stores/chat"
import { Bot, User } from "lucide-react"

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
        <div className="mt-1 whitespace-pre-wrap break-words text-sm font-normal">
          {message.content}
        </div>
      </ItemContent>
    </Item>
  )
}
