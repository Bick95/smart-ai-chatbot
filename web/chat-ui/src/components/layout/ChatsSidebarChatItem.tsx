"use client";

import { Link, useLocation } from "react-router-dom";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenuButton } from "@/components/ui/sidebar";
import { useAuthStore } from "@/stores/auth";
import type { ChatResponseItem } from "@/stores/stateful-chat/schemas";
import type { ResourceManagementTab } from "@/components/resource-management/ResourceManagement";
import { FileText, MoreHorizontal } from "lucide-react";

function isOwner(ownerSubject: string): boolean {
    const user = useAuthStore.getState().user;
    if (!user) return false;
    return ownerSubject === `user:${user.id}`;
}

export interface ChatsSidebarChatItemProps {
    chat: ChatResponseItem;
    depth: number;
    onManageOpen: (
        type: "chat" | "folder",
        id: string,
        name?: string,
        defaultTab?: ResourceManagementTab
    ) => void;
}

export function ChatsSidebarChatItem({
    chat,
    depth,
    onManageOpen,
}: ChatsSidebarChatItemProps) {
    const location = useLocation();
    const isActive = location.pathname === `/chats/${chat.id}`;

    return (
        <div
            className="flex items-center gap-1"
            style={{ paddingLeft: `${depth * 12}px` }}
        >
            <span className="h-6 w-6 shrink-0" />
            <Link
                to={`/chats/${chat.id}`}
                className="min-w-0 flex-1 truncate"
            >
                <SidebarMenuButton
                    isActive={isActive}
                    className="w-full justify-start"
                >
                    <FileText className="size-4 shrink-0" />
                    <span className="truncate">
                        {chat.title || "Untitled chat"}
                    </span>
                </SidebarMenuButton>
            </Link>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <button
                        type="button"
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded hover:bg-sidebar-accent"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <MoreHorizontal className="size-4" />
                    </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                    <DropdownMenuItem
                        onClick={() =>
                            onManageOpen("chat", chat.id, chat.title ?? undefined, "permissions")
                        }
                    >
                        Share
                    </DropdownMenuItem>
                    <DropdownMenuItem
                        onClick={() =>
                            onManageOpen("chat", chat.id, chat.title ?? undefined, "name")
                        }
                    >
                        Rename
                    </DropdownMenuItem>
                    <DropdownMenuItem
                        onClick={() =>
                            onManageOpen("chat", chat.id, chat.title ?? undefined, "parent")
                        }
                    >
                        Move
                    </DropdownMenuItem>
                    {isOwner(chat.owner_subject) && (
                        <DropdownMenuItem
                            onClick={() =>
                                onManageOpen("chat", chat.id, chat.title ?? undefined, "destructive")
                            }
                        >
                            Delete
                        </DropdownMenuItem>
                    )}
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}
