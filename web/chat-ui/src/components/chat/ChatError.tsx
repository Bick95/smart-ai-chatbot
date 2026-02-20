import {
    Item,
    ItemActions,
    ItemContent,
    ItemMedia,
    ItemTitle,
} from "@/components/ui/item"
import { Button } from "@/components/ui/button"
import { AlertCircle, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ChatErrorProps {
    message: string
    onRetry: () => void
    isRetrying?: boolean
    className?: string
}

export function ChatError({
    message,
    onRetry,
    isRetrying = false,
    className,
}: ChatErrorProps) {
    return (
        <Item
            variant="outline"
            size="default"
            className={cn(
                "w-fit max-w-[95%] border-destructive/50 bg-destructive/10 self-start rounded-2xl",
                className
            )}
        >
            <ItemMedia variant="icon" className="bg-destructive/20">
                <AlertCircle className="size-4 text-destructive" aria-hidden />
            </ItemMedia>
            <ItemContent className="min-w-0 flex-1">
                <ItemTitle className="text-destructive text-sm font-medium">
                    Request failed
                </ItemTitle>
                <p className="text-muted-foreground mt-0.5 text-sm">{message}</p>
            </ItemContent>
            <ItemActions>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={onRetry}
                    disabled={isRetrying}
                    className="gap-1.5"
                >
                    <RotateCcw
                        className={cn("size-4", isRetrying && "animate-spin")}
                        aria-hidden
                    />
                    Resubmit
                </Button>
            </ItemActions>
        </Item>
    )
}
