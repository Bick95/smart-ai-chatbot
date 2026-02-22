import { useCallback, useState } from "react";
import "./App.css";
import { sendChatMessages } from "@/api/stateless_chat";
import { ChatUI } from "@/components/chat";
import { useChatStore } from "@/stores/chat";

export default function App() {
    const [error, setError] = useState<{ message: string } | null>(null);
    const [isRetrying, setIsRetrying] = useState(false);

    const onSendMessage = useCallback(async (content: string) => {
        setError(null);
        const store = useChatStore.getState();
        store.addMessageToCurrent({ role: "user", content });
        const chat = store.getCurrentChat();
        const chatId = store.currentChatId;
        if (!chatId || !chat) return;

        const apiMessages = chat.messages.map((m) => ({
            role: m.role,
            content: m.content,
        }));

        try {
            const reply = await sendChatMessages(apiMessages);
            store.addMessage(chatId, {
                role: "assistant",
                content: reply,
            });
        } catch (err) {
            setError({
                message: err instanceof Error ? err.message : String(err),
            });
        }
    }, []);

    const onRetry = useCallback(async () => {
        setIsRetrying(true);
        setError(null);
        const store = useChatStore.getState();
        const chat = store.getCurrentChat();
        const chatId = store.currentChatId;
        if (!chatId || !chat) {
            setIsRetrying(false);
            return;
        }

        const apiMessages = chat.messages.map((m) => ({
            role: m.role,
            content: m.content,
        }));

        try {
            const reply = await sendChatMessages(apiMessages);
            store.addMessage(chatId, {
                role: "assistant",
                content: reply,
            });
        } catch (err) {
            setError({
                message: err instanceof Error ? err.message : String(err),
            });
        } finally {
            setIsRetrying(false);
        }
    }, []);

    return (
        <ChatUI
            onSendMessage={onSendMessage}
            error={error}
            onRetry={onRetry}
            isRetrying={isRetrying}
        />
    );
}
