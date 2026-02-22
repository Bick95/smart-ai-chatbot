import type { AnchorHTMLAttributes } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Item, ItemContent, ItemMedia, ItemTitle } from "@/components/ui/item";
import { cn } from "@/lib/utils";
import type { Message } from "@/stores/chat";
import { Bot, User } from "lucide-react";

function formatMessageTime(date: Date): string {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const msgDate = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate(),
    );
    const time = date.toLocaleTimeString("de-DE", {
        hour: "2-digit",
        minute: "2-digit",
    });
    if (msgDate.getTime() === today.getTime()) {
        return time;
    }
    if (msgDate.getTime() === yesterday.getTime()) {
        return `Yesterday, ${time}`;
    }
    const dateStr = date.toLocaleDateString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    });
    return `${dateStr}, ${time}`;
}

function SafeLink({
    href,
    children,
    ...props
}: AnchorHTMLAttributes<HTMLAnchorElement>) {
    const url = String(href ?? "");
    // Only allow protocols that navigate or open apps; block javascript:, data:, vbscript:, etc.,
    // which execute code when clicked and can lead to XSS.
    const isSafe =
        url.startsWith("http://") ||
        url.startsWith("https://") ||
        url.startsWith("mailto:");

    if (!isSafe) return <span>{children}</span>;

    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer nofollow"
            {...props}
        >
            {children}
        </a>
    );
}

export interface ChatMessageProps {
    message: Message;
    className?: string;
}

export function ChatMessage({ message, className }: ChatMessageProps) {
    const isUser = message.role === "user";

    return (
        <Item
            variant={isUser ? "default" : "muted"}
            size="default"
            className={cn(
                "w-fit max-w-[95%] rounded-2xl",
                isUser
                    ? "ml-auto flex-row-reverse border border-border bg-muted/80 text-foreground"
                    : "mr-auto flex-row bg-muted text-foreground",
                className,
            )}
        >
            <ItemMedia variant="icon">
                {isUser ? (
                    <User className="size-4" aria-hidden />
                ) : (
                    <Bot className="size-4" aria-hidden />
                )}
            </ItemMedia>
            <ItemContent
                className={cn("min-w-0 flex-1", isUser && "text-right")}
            >
                <div
                    className={cn(
                        "flex items-center gap-2",
                        isUser && "justify-end",
                    )}
                >
                    <ItemTitle className="text-xs font-medium opacity-80">
                        {isUser ? "You" : "Assistant"}
                    </ItemTitle>
                    {message.createdAt && (
                        <time
                            dateTime={message.createdAt.toISOString()}
                            className="text-muted-foreground text-xs opacity-70"
                        >
                            {formatMessageTime(message.createdAt)}
                        </time>
                    )}
                </div>
                <div className="markdown-content mt-1 max-w-none break-words text-sm font-normal">
                    {
                        /* remarkGfm adds GitHub Flavored Markdown: tables, strikethrough, task lists,
                           autolinks, which are common in LLM output.
                        */
                    }
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
    );
}
