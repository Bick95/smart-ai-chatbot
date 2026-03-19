import { useEffect } from "react";
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

export default function App() {
    const hydrate = useAuthStore((s) => s.hydrate);

    useEffect(() => {
        hydrate();
    }, [hydrate]);

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
