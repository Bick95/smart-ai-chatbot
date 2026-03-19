"use client";

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
    SidebarGroup,
    SidebarGroupContent,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import type { ResourceManagementTab } from "@/components/resource-management/ResourceManagement";
import { ResourceManagement } from "@/components/resource-management/ResourceManagement";
import { ChatsSidebarChatItem } from "./ChatsSidebarChatItem";
import { ChatsSidebarFolderItem } from "./ChatsSidebarFolderItem";
import { Plus } from "lucide-react";

interface ManageState {
    type: "chat" | "folder";
    id: string;
    name?: string;
    defaultTab: ResourceManagementTab;
}

export function ChatsSidebar() {
    const store = useStatefulChatStore();
    const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
        new Set()
    );
    const [manageState, setManageState] = useState<ManageState | null>(null);

    const rootFolders = store.foldersByParent["root"] ?? [];
    const rootChats = store.recentChats.filter((c) => !c.folder_id);
    const rootNextCursor = store.recentChatsNextCursor;

    useEffect(() => {
        store.loadChats(null);
        store.loadFolders(null);
    }, [store]);

    const toggleFolder = useCallback((folderId: string) => {
        setExpandedFolders((prev) => {
            const next = new Set(prev);
            if (next.has(folderId)) {
                next.delete(folderId);
            } else {
                next.add(folderId);
            }
            return next;
        });
    }, []);

    const handleManageOpen = useCallback(
        (
            type: "chat" | "folder",
            id: string,
            name?: string,
            defaultTab: ResourceManagementTab = "name"
        ) => {
            setManageState({ type, id, name, defaultTab });
        },
        []
    );

    return (
        <>
            <SidebarGroup>
                <SidebarGroupContent>
                    <SidebarMenu>
                        <SidebarMenuItem>
                            <SidebarMenuButton asChild>
                                <Link to="/chats?new=1">
                                    <Plus className="size-4" />
                                    <span>New chat</span>
                                </Link>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                        {rootFolders.map((f) => (
                            <ChatsSidebarFolderItem
                                key={f.id}
                                folder={f}
                                depth={0}
                                expandedFolders={expandedFolders}
                                onToggle={toggleFolder}
                                foldersByParent={store.foldersByParent}
                                folderChatsByFolderId={
                                    store.folderChatsByFolderId
                                }
                                onLoadMoreChats={(folderId, cursor) =>
                                    store.loadChats(folderId, cursor)
                                }
                                onManageOpen={handleManageOpen}
                                onLoadFolders={(parentId) =>
                                    store.loadFolders(parentId)
                                }
                                onLoadChats={(folderId, cursor) =>
                                    store.loadChats(folderId, cursor)
                                }
                            />
                        ))}
                        {rootChats.map((c) => (
                            <ChatsSidebarChatItem
                                key={c.id}
                                chat={c}
                                depth={0}
                                onManageOpen={handleManageOpen}
                            />
                        ))}
                        {rootNextCursor && (
                            <SidebarMenuItem>
                                <button
                                    type="button"
                                    className="text-muted-foreground w-full px-2 py-1 text-left text-sm hover:underline"
                                    onClick={() =>
                                        store.loadChats(null, rootNextCursor)
                                    }
                                >
                                    Load more
                                </button>
                            </SidebarMenuItem>
                        )}
                    </SidebarMenu>
                </SidebarGroupContent>
            </SidebarGroup>
            {manageState && (
                <ResourceManagement
                    resourceType={manageState.type}
                    resourceId={manageState.id}
                    resourceName={manageState.name}
                    variant="popup"
                    defaultTab={manageState.defaultTab}
                    open={true}
                    onClose={() => setManageState(null)}
                    onUpdated={() => setManageState(null)}
                />
            )}
        </>
    );
}
