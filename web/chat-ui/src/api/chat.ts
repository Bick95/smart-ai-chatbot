/**
 * Base URL for the chatbot API (no trailing slash).
 * Defaults to empty string = same-origin (use Vite proxy in dev).
 * Set VITE_CHATBOT_API_URL to override (e.g. http://localhost:8000).
 */
const API_BASE = import.meta.env.VITE_CHATBOT_API_URL ?? "";

export interface ChatApiMessage {
    role: "user" | "assistant" | "system";
    content: string;
}

export interface ChatApiRequest {
    messages: ChatApiMessage[];
}

export interface ChatApiResponse {
    content: string;
}

/**
 * Send messages to the stateless chat API and receive the assistant's reply.
 * The backend expects the full conversation history each request.
 */
export async function sendChatMessages(
    messages: Array<{ role: string; content: string }>,
): Promise<string> {
    const body: ChatApiRequest = {
        messages: messages.map((m) => ({
            role: m.role as ChatApiMessage["role"],
            content: m.content,
        })),
    };

    const res = await fetch(`${API_BASE}/api/v1/stateless_chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(
            `Chat API error (${res.status}): ${text || res.statusText}`,
        );
    }

    const data: ChatApiResponse = await res.json();
    return data.content;
}
