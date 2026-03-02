import { API_BASE } from "../constants";
import {
    type ChatApiMessage,
    type ChatApiRequest,
    type ChatApiResponse,
    chatApiRequestSchema,
    chatApiResponseSchema,
} from "../stores/chat/schemas";

/**
 * Send messages to the stateless chat API and receive the assistant's reply.
 * The backend expects the full conversation history each request.
 * Validates both the outgoing request and incoming response.
 * Pass authToken when the user is signed in (required by the backend).
 */
export async function sendChatMessages(
    messages: ChatApiMessage[],
    authToken?: string
): Promise<string> {
    const body: ChatApiRequest = chatApiRequestSchema.parse({
        messages,
    });

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${API_BASE}/api/v1/stateless_chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(
            `Chat API error (${res.status}): ${text || res.statusText}`,
        );
    }

    const json: unknown = await res.json();
    const data: ChatApiResponse = chatApiResponseSchema.parse(json);
    return data.content;
}
