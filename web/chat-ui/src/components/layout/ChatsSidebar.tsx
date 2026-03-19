"use client";

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    DndContext,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
} from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";

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
import {
    ChatsSidebarFolderItem,
    DROP_FOLDER_PREFIX,
    DROP_ROOT,
} from "./ChatsSidebarFolderItem";
import { Plus } from "lucide-react";

function RootDropZone() {
    const { setNodeRef, isOver } = useDroppable({
        id: DROP_ROOT,
        data: { type: "root" as const },
    });
    return (
        <div
            ref={setNodeRef}
            className={`mb-1 min-h-6 rounded px-2 py-1 text-muted-foreground text-xs transition-colors ${isOver ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}`}
            aria-label="Drop to move to root"
        >
            Root
        </div>
    );
}

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

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: { distance: 8 },
        })
    );

    const handleDragEnd = useCallback((event: DragEndEvent) => {
            const { active, over } = event;
            if (!over) return;

            const activeData = active.data?.current as { type?: string; id?: string } | undefined;
            if (!activeData?.id || !activeData?.type) return;

            const overId = String(over.id);
            let targetFolderId: string | null;
            const overData = over.data?.current as { folderId?: string } | undefined;
            if (overId === DROP_ROOT) {
                targetFolderId = null;
            } else if (overId.startsWith(DROP_FOLDER_PREFIX)) {
                targetFolderId = overData?.folderId ?? overId.slice(DROP_FOLDER_PREFIX.length);
            } else {
                return;
            }

            if (activeData.type === "chat") {
                store.moveChatToFolder(activeData.id, targetFolderId);
            } else if (activeData.type === "folder") {
                if (targetFolderId === activeData.id) return;
                const foldersByParent = store.foldersByParent;
                const isDescendant = (ancestorId: string, nodeId: string): boolean => {
                    if (ancestorId === nodeId) return true;
                    const children = foldersByParent[ancestorId] ?? [];
                    for (const c of children) {
                        if (c.id === nodeId) return true;
                        if (isDescendant(c.id, nodeId)) return true;
                    }
                    return false;
                };
                if (targetFolderId && isDescendant(activeData.id, targetFolderId)) return;
                store.moveFolderToParent(activeData.id, targetFolderId);
            }
        },
        [store]
    );

    return (
        <>
            <SidebarGroup>
                <SidebarGroupContent>
                    <DndContext
                        sensors={sensors}
                        onDragEnd={handleDragEnd}
                    >
                        <RootDropZone />
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
                    </DndContext>
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
