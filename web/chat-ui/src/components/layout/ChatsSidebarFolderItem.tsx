"use client";

import { Link, useLocation } from "react-router-dom";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenuButton } from "@/components/ui/sidebar";
import { useAuthStore } from "@/stores/auth";
import type {
    ChatResponseItem,
    FolderResponseItem,
} from "@/stores/stateful-chat/schemas";
import type { ResourceManagementTab } from "@/components/resource-management/ResourceManagement";
import {
    ChevronDown,
    ChevronRight,
    Folder,
    MessageSquarePlus,
    MoreHorizontal,
} from "lucide-react";
import { ChatsSidebarChatItem } from "./ChatsSidebarChatItem";

function isOwner(ownerSubject: string): boolean {
    const user = useAuthStore.getState().user;
    if (!user) return false;
    return ownerSubject === `user:${user.id}`;
}

export const DROP_ROOT = "drop-root";
export const DROP_FOLDER_PREFIX = "drop-folder-";
export const DRAG_FOLDER_PREFIX = "drag-folder-";

export interface ChatsSidebarFolderItemProps {
    folder: FolderResponseItem;
    depth: number;
    expandedFolders: Set<string>;
    onToggle: (folderId: string) => void;
    foldersByParent: Record<string | "root", FolderResponseItem[]>;
    folderChatsByFolderId: Record<
        string,
        { items: ChatResponseItem[]; nextCursor: string | null }
    >;
    onLoadMoreChats: (folderId: string, cursor: string) => void;
    onManageOpen: (
        type: "chat" | "folder",
        id: string,
        name?: string,
        defaultTab?: ResourceManagementTab
    ) => void;
    onLoadFolders: (parentId: string) => void;
    onLoadChats: (folderId: string, cursor?: string | null) => void;
    draggable?: boolean;
}

export function ChatsSidebarFolderItem({
    folder,
    depth,
    expandedFolders,
    onToggle,
    foldersByParent,
    folderChatsByFolderId,
    onLoadMoreChats,
    onManageOpen,
    onLoadFolders,
    onLoadChats,
    draggable = true,
}: ChatsSidebarFolderItemProps) {
    const location = useLocation();
    const isExpanded = expandedFolders.has(folder.id);
    const canDrag = draggable && isOwner(folder.owner_subject);

    const {
        attributes,
        listeners,
        setNodeRef: setDraggableRef,
        transform,
        isDragging,
    } = useDraggable({
        id: `${DRAG_FOLDER_PREFIX}${folder.id}`,
        data: { type: "folder" as const, id: folder.id },
        disabled: !canDrag,
    });

    const { setNodeRef: setDroppableRef, isOver } = useDroppable({
        id: `${DROP_FOLDER_PREFIX}${folder.id}`,
        data: { type: "folder" as const, folderId: folder.id },
    });

    const setNodeRef = (node: HTMLDivElement | null) => {
        setDraggableRef(node);
        setDroppableRef(node);
    };

    const dragStyle = transform
        ? { transform: CSS.Translate.toString(transform) }
        : undefined;
    const childFolders = foldersByParent[folder.id] ?? [];
    const folderChats = folderChatsByFolderId[folder.id] ?? {
        items: [],
        nextCursor: null,
    };
    const isActive = location.pathname === `/chats/folders/${folder.id}`;

    const handleToggle = () => {
        if (!isExpanded) {
            onLoadFolders(folder.id);
            onLoadChats(folder.id);
        }
        onToggle(folder.id);
    };

    return (
        <div className="flex flex-col">
            <div
                ref={setNodeRef}
                style={{ ...dragStyle, paddingLeft: `${depth * 12}px` }}
                className={`flex items-center gap-1 ${isDragging ? "opacity-50" : ""} ${isOver ? "ring-1 ring-primary rounded" : ""} ${canDrag ? "cursor-grab active:cursor-grabbing" : ""}`}
                {...(canDrag ? { ...listeners, ...attributes } : {})}
            >
                <button
                    type="button"
                    onClick={handleToggle}
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded hover:bg-sidebar-accent"
                >
                    {isExpanded ? (
                        <ChevronDown className="size-4" />
                    ) : (
                        <ChevronRight className="size-4" />
                    )}
                </button>
                <Link
                    to={`/chats/folders/${folder.id}`}
                    className="min-w-0 flex-1 truncate"
                >
                    <SidebarMenuButton
                        isActive={isActive}
                        className="w-full justify-start"
                    >
                        <Folder className="size-4 shrink-0" />
                        <span className="truncate">{folder.name}</span>
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
                                onManageOpen("folder", folder.id, folder.name, "permissions")
                            }
                        >
                            Share
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                            <Link to={`/chats?new=1&folderId=${folder.id}`}>
                                <MessageSquarePlus className="mr-2 size-4" />
                                New chat in folder
                            </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                            onClick={() =>
                                onManageOpen("folder", folder.id, folder.name, "name")
                            }
                        >
                            Rename
                        </DropdownMenuItem>
                        <DropdownMenuItem
                            onClick={() =>
                                onManageOpen("folder", folder.id, folder.name, "parent")
                            }
                        >
                            Move
                        </DropdownMenuItem>
                        {isOwner(folder.owner_subject) && (
                            <DropdownMenuItem
                                onClick={() =>
                                    onManageOpen(
                                        "folder",
                                        folder.id,
                                        folder.name,
                                        "destructive"
                                    )
                                }
                            >
                                Delete
                            </DropdownMenuItem>
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
            {isExpanded && (
                <div className="flex flex-col">
                    {childFolders.map((f) => (
                        <ChatsSidebarFolderItem
                            key={f.id}
                            folder={f}
                            depth={depth + 1}
                            expandedFolders={expandedFolders}
                            onToggle={onToggle}
                            foldersByParent={foldersByParent}
                            folderChatsByFolderId={folderChatsByFolderId}
                            onLoadMoreChats={onLoadMoreChats}
                            onManageOpen={onManageOpen}
                            onLoadFolders={onLoadFolders}
                            onLoadChats={onLoadChats}
                        />
                    ))}
                    {folderChats.items.map((chat) => (
                        <ChatsSidebarChatItem
                            key={chat.id}
                            chat={chat}
                            depth={depth + 1}
                            onManageOpen={onManageOpen}
                        />
                    ))}
                    {folderChats.nextCursor && (
                        <button
                            type="button"
                            className="text-muted-foreground px-4 py-1 text-left text-sm hover:underline"
                            style={{
                                paddingLeft: `${(depth + 1) * 12 + 28}px`,
                            }}
                            onClick={() =>
                                onLoadMoreChats(folder.id, folderChats.nextCursor!)
                            }
                        >
                            Load more
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
