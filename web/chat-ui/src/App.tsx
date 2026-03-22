import { useEffect, useRef } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppLayout } from "@/components/layout";
import {
    ChatPage,
    DashboardPage,
    FolderViewPage,
    LoginPage,
    SignupPage,
    StatefulChatPage,
} from "@/pages";
import { useAuthStore } from "@/stores/auth";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import { useChatStore } from "@/stores/chat";

export default function App() {
    const hydrate = useAuthStore((s) => s.hydrate);
    const prevUserIdRef = useRef<string | null>(null);

    useEffect(() => {
        hydrate();
    }, [hydrate]);

    useEffect(() => {
        const unsub = useAuthStore.subscribe(() => {
            const current = useAuthStore.getState().user?.id ?? null;
            if (current !== prevUserIdRef.current) {
                prevUserIdRef.current = current;
                useStatefulChatStore.getState().reset();
                useChatStore.getState().resetTemporaryChat();
            }
        });
        prevUserIdRef.current = useAuthStore.getState().user?.id ?? null;
        return unsub;
    }, []);

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />
                <Route element={<AppLayout />}>
                    <Route path="/" element={<Navigate to="/chat" replace />} />
                    <Route
                        path="/chat"
                        element={
                            <ProtectedRoute>
                                <ChatPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chats"
                        element={
                            <ProtectedRoute>
                                <StatefulChatPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chats/:chatId"
                        element={
                            <ProtectedRoute>
                                <StatefulChatPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chats/folders/:folderId"
                        element={
                            <ProtectedRoute>
                                <FolderViewPage />
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/dashboard"
                        element={
                            <ProtectedRoute>
                                <DashboardPage />
                            </ProtectedRoute>
                        }
                    />
                </Route>
                <Route path="*" element={<Navigate to="/chat" replace />} />
            </Routes>
        </BrowserRouter>
    );
}
