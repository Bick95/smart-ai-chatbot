"use client";

import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    DndContext,
    PointerSensor,
    useSensor,
    useSensors,
    useDroppable,
} from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useAuthStore } from "@/stores/auth";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import type { ResourceManagementTab } from "@/components/resource-management/ResourceManagement";
import { ResourceManagement } from "@/components/resource-management/ResourceManagement";
import { ChatsSidebarChatItem } from "./ChatsSidebarChatItem";
import {
    ChatsSidebarFolderItem,
    DROP_FOLDER_PREFIX,
    DROP_ROOT,
} from "./ChatsSidebarFolderItem";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight, FolderPlus, Plus } from "lucide-react";

function RootDropZone() {
    const { setNodeRef, isOver } = useDroppable({
        id: DROP_ROOT,
        data: { type: "root" as const },
    });
    return (
        <div
            ref={setNodeRef}
            className={`mb-1 min-h-6 rounded-md px-2 py-1.5 text-muted-foreground text-xs transition-colors ${isOver ? "bg-sidebar-accent text-sidebar-accent-foreground" : ""}`}
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
    const user = useAuthStore((s) => s.user);
    const loadChats = useStatefulChatStore((s) => s.loadChats);
    const loadFolders = useStatefulChatStore((s) => s.loadFolders);
    const loadSharedWithMeChats = useStatefulChatStore(
        (s) => s.loadSharedWithMeChats
    );
    const sharedWithMeChats = useStatefulChatStore((s) => s.sharedWithMeChats);
    const sharedWithMeNextCursor = useStatefulChatStore(
        (s) => s.sharedWithMeNextCursor
    );
    const createFolder = useStatefulChatStore((s) => s.createFolder);
    const expandedFolderIds = useStatefulChatStore((s) => s.expandedFolderIds);
    const toggleExpandedFolder = useStatefulChatStore(
        (s) => s.toggleExpandedFolder
    );
    const ensureFolderExpanded = useStatefulChatStore(
        (s) => s.ensureFolderExpanded
    );
    const { folderId: routeFolderId } = useParams<{ folderId?: string }>();
    const [manageState, setManageState] = useState<ManageState | null>(null);
    const [newFolderOpen, setNewFolderOpen] = useState(false);
    const [newFolderParentId, setNewFolderParentId] = useState<string | null>(
        null
    );
    const [newFolderName, setNewFolderName] = useState("");
    const [newFolderCreating, setNewFolderCreating] = useState(false);
    const [sharedWithMeExpanded, setSharedWithMeExpanded] = useState(true);

    const rootFolders = store.foldersByParent["root"] ?? [];
    const rootChats = store.recentChats.filter((c) => {
        if (c.folder_id) return false;
        if (!user) return true;
        return c.owner_subject === `user:${user.id}`;
    });
    const rootNextCursor = store.recentChatsNextCursor;

    useEffect(() => {
        loadChats(null);
        loadFolders(null);
        loadSharedWithMeChats();
    }, [loadChats, loadFolders, loadSharedWithMeChats]);

    useEffect(() => {
        if (routeFolderId) {
            ensureFolderExpanded(routeFolderId);
        }
    }, [routeFolderId, ensureFolderExpanded]);

    useEffect(() => {
        for (const folderId of expandedFolderIds) {
            loadFolders(folderId);
            loadChats(folderId);
        }
    }, [expandedFolderIds, loadFolders, loadChats]);

    const toggleFolder = useCallback(
        (folderId: string) => {
            toggleExpandedFolder(folderId);
        },
        [toggleExpandedFolder]
    );

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

    const handleCreateFolder = useCallback(async () => {
        const name = newFolderName.trim();
        if (!name) return;
        setNewFolderCreating(true);
        try {
            await createFolder(name, newFolderParentId);
            setNewFolderOpen(false);
            setNewFolderName("");
            setNewFolderParentId(null);
            loadFolders(null);
            if (newFolderParentId) loadFolders(newFolderParentId);
        } finally {
            setNewFolderCreating(false);
        }
    }, [newFolderName, newFolderParentId, createFolder, loadFolders]);

    const openNewFolderDialog = useCallback((parentId: string | null) => {
        setNewFolderParentId(parentId);
        setNewFolderName("");
        setNewFolderOpen(true);
    }, []);

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
                <SidebarGroupLabel>Chats</SidebarGroupLabel>
                <SidebarGroupContent>
                    <DndContext
                        sensors={sensors}
                        onDragEnd={handleDragEnd}
                    >
                        <SidebarMenu className="gap-1 mb-1">
                            <SidebarMenuItem>
                                <SidebarMenuButton asChild>
                                    <Link to="/chats?new=1">
                                        <Plus className="size-4" />
                                        <span>New chat</span>
                                    </Link>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                            <SidebarMenuItem>
                                <SidebarMenuButton
                                    onClick={() => openNewFolderDialog(null)}
                                >
                                    <FolderPlus className="size-4" />
                                    <span>New folder</span>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </SidebarMenu>
                        <div className="mb-1">
                            <button
                                type="button"
                                className="flex w-full items-center gap-1 rounded-md px-2 py-1.5 text-left text-muted-foreground text-xs transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                                onClick={() =>
                                    setSharedWithMeExpanded((e) => !e)
                                }
                                aria-expanded={sharedWithMeExpanded}
                            >
                                {sharedWithMeExpanded ? (
                                    <ChevronDown className="size-3.5 shrink-0" />
                                ) : (
                                    <ChevronRight className="size-3.5 shrink-0" />
                                )}
                                <span className="font-medium">
                                    Shared with me
                                </span>
                            </button>
                            {sharedWithMeExpanded && (
                                <SidebarMenu className="gap-1 mt-0.5">
                                    {sharedWithMeChats.map((c) => (
                                        <ChatsSidebarChatItem
                                            key={c.id}
                                            chat={c}
                                            depth={0}
                                            onManageOpen={handleManageOpen}
                                        />
                                    ))}
                                    {sharedWithMeChats.length === 0 && (
                                        <p className="px-2 py-1 text-muted-foreground text-xs">
                                            No chats shared with you yet.
                                        </p>
                                    )}
                                    {sharedWithMeNextCursor && (
                                        <SidebarMenuItem>
                                            <button
                                                type="button"
                                                className="text-muted-foreground w-full px-2 py-1 text-left text-sm hover:underline"
                                                onClick={() =>
                                                    loadSharedWithMeChats(
                                                        sharedWithMeNextCursor
                                                    )
                                                }
                                            >
                                                Load more
                                            </button>
                                        </SidebarMenuItem>
                                    )}
                                </SidebarMenu>
                            )}
                        </div>
                        <RootDropZone />
                        <SidebarMenu className="gap-1">
                        {rootFolders.map((f) => (
                            <ChatsSidebarFolderItem
                                key={f.id}
                                folder={f}
                                depth={0}
                                expandedFolders={expandedFolderIds}
                                onToggle={toggleFolder}
                                foldersByParent={store.foldersByParent}
                                folderChatsByFolderId={
                                    store.folderChatsByFolderId
                                }
                                onLoadMoreChats={(folderId, cursor) =>
                                    store.loadChats(folderId, cursor)
                                }
                                onManageOpen={handleManageOpen}
                                onCreateSubfolder={openNewFolderDialog}
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
            <Dialog
                open={newFolderOpen}
                onOpenChange={(open) => {
                    setNewFolderOpen(open);
                    if (!open) {
                        setNewFolderName("");
                        setNewFolderParentId(null);
                    }
                }}
            >
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>
                            {newFolderParentId
                                ? "New subfolder"
                                : "New folder"}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label htmlFor="new-folder-name">Name</Label>
                            <Input
                                id="new-folder-name"
                                value={newFolderName}
                                onChange={(e) =>
                                    setNewFolderName(e.target.value)
                                }
                                placeholder="Folder name"
                                onKeyDown={(e) =>
                                    e.key === "Enter" && handleCreateFolder()
                                }
                            />
                        </div>
                        <Button
                            onClick={handleCreateFolder}
                            disabled={
                                !newFolderName.trim() || newFolderCreating
                            }
                        >
                            {newFolderCreating ? "Creating…" : "Create"}
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
}
