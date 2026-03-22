"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import { searchUsers } from "@/api/stateful_chat";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2 } from "lucide-react";

export type ResourceManagementTab =
    | "name"
    | "parent"
    | "permissions"
    | "systemPrompt"
    | "destructive";

export interface ResourceManagementProps {
    resourceType: "chat" | "folder";
    resourceId: string;
    resourceName?: string;
    variant: "inline" | "popup";
    defaultTab?: ResourceManagementTab;
    open?: boolean;
    onClose?: () => void;
    onUpdated?: () => void;
}

function isOwner(ownerSubject: string): boolean {
    const user = useAuthStore.getState().user;
    if (!user) return false;
    return ownerSubject === `user:${user.id}`;
}

export function ResourceManagement({
    resourceType,
    resourceId,
    resourceName = "",
    variant,
    defaultTab = "name",
    open = true,
    onClose,
    onUpdated,
}: ResourceManagementProps) {
    const [activeTab, setActiveTab] = useState<ResourceManagementTab>(defaultTab);
    const [nameValue, setNameValue] = useState(resourceName);
    const [systemPromptValue, setSystemPromptValue] = useState("");
    const [parentId, setParentId] = useState<string | null>(null);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [shareSearchQuery, setShareSearchQuery] = useState("");
    const [shareSearchResults, setShareSearchResults] = useState<
        { id: string; username: string }[]
    >([]);
    const [shareRole, setShareRole] = useState<"viewer" | "editor">("editor");

    const store = useStatefulChatStore();
    const loadFolder = useStatefulChatStore((s) => s.loadFolder);
    const loadFolders = useStatefulChatStore((s) => s.loadFolders);
    const loadShares = useStatefulChatStore((s) => s.loadShares);
    const chat = resourceType === "chat" ? store.chats[resourceId] : null;
    const folder =
        resourceType === "folder"
            ? store.currentFolder ??
              Object.values(store.foldersByParent)
                  .flat()
                  .find((f) => f.id === resourceId)
            : null;
    const ownerSubject =
        resourceType === "chat"
            ? chat?.owner_subject
            : folder?.owner_subject ?? "";
    const isOwnerUser = isOwner(ownerSubject ?? "");
    const shares = store.sharesByChatId[resourceId] ?? [];

    useEffect(() => {
        setActiveTab(defaultTab);
    }, [defaultTab]);

    useEffect(() => {
        setNameValue(resourceName || chat?.title || folder?.name || "");
        setSystemPromptValue(folder?.system_prompt ?? "");
        setParentId(
            resourceType === "chat"
                ? chat?.folder_id ?? null
                : folder?.parent_id ?? null
        );
    }, [resourceId, resourceName, chat, folder, resourceType]);

    useEffect(() => {
        if (resourceType === "folder") {
            loadFolder(resourceId);
        }
    }, [resourceId, resourceType, loadFolder]);

    useEffect(() => {
        if (activeTab === "parent") {
            loadFolders(null);
        }
    }, [activeTab, loadFolders]);

    useEffect(() => {
        if (resourceType === "chat" && activeTab === "permissions") {
            loadShares(resourceId);
        }
    }, [resourceId, resourceType, activeTab, loadShares]);

    const handleSaveName = useCallback(async () => {
        if (resourceType === "chat") {
            await store.updateChat(resourceId, { title: nameValue });
        } else {
            await store.updateFolder(resourceId, { name: nameValue });
        }
        onUpdated?.();
    }, [resourceId, resourceType, nameValue, store, onUpdated]);

    const handleSaveSystemPrompt = useCallback(async () => {
        if (resourceType !== "folder") return;
        await store.updateFolder(resourceId, {
            system_prompt: systemPromptValue || null,
        });
        onUpdated?.();
    }, [resourceId, resourceType, systemPromptValue, store, onUpdated]);

    const handleMove = useCallback(
        async (targetFolderId: string | null) => {
            if (resourceType === "chat") {
                await store.moveChatToFolder(resourceId, targetFolderId);
            } else {
                await store.moveFolderToParent(resourceId, targetFolderId);
            }
            setParentId(targetFolderId);
            onUpdated?.();
        },
        [resourceId, resourceType, store, onUpdated]
    );

    const handleDelete = useCallback(async () => {
        if (resourceType === "chat") {
            await store.deleteChat(resourceId);
        } else {
            await store.deleteFolder(resourceId);
        }
        setDeleteConfirmOpen(false);
        onClose?.();
        onUpdated?.();
    }, [resourceId, resourceType, store, onClose, onUpdated]);

    const handleSearchUsers = useCallback(async () => {
        if (!shareSearchQuery.trim()) return;
        try {
            const users = await searchUsers(
                shareSearchQuery,
                10,
                useAuthStore.getState().authToken ?? undefined
            );
            setShareSearchResults(users);
        } catch {
            setShareSearchResults([]);
        }
    }, [shareSearchQuery]);

    const handleAddShare = useCallback(
        async (userId: string) => {
            await store.addShare(resourceId, "user", userId, shareRole);
            store.loadShares(resourceId);
            setShareSearchQuery("");
            setShareSearchResults([]);
            onUpdated?.();
        },
        [resourceId, store, shareRole, onUpdated]
    );

    const handleRemoveShare = useCallback(
        async (subject: string) => {
            const [type, id] = subject.split(":");
            if (type && id) {
                await store.removeShare(resourceId, type, id);
                store.loadShares(resourceId);
                onUpdated?.();
            }
        },
        [resourceId, store, onUpdated]
    );

    const tabTriggers: { id: ResourceManagementTab; label: string }[] = [
        { id: "name", label: "Name" },
        { id: "parent", label: "Parent" },
        { id: "permissions", label: "Permissions" },
        ...(resourceType === "folder"
            ? [{ id: "systemPrompt" as const, label: "System prompt" }]
            : []),
        ...(isOwnerUser
            ? [{ id: "destructive" as const, label: "Destructive" }]
            : []),
    ];

    const content = (
        <Tabs
            value={activeTab}
            onValueChange={(v) => setActiveTab(v as ResourceManagementTab)}
        >
            <TabsList className="flex h-auto flex-wrap gap-1 p-1">
                {tabTriggers.map((t) => (
                    <TabsTrigger key={t.id} value={t.id}>
                        {t.label}
                    </TabsTrigger>
                ))}
            </TabsList>

            <TabsContent value="name" className="space-y-4 pt-4">
                <div className="space-y-2">
                    <Label htmlFor="resource-name">Name</Label>
                    <Input
                        id="resource-name"
                        value={nameValue}
                        onChange={(e) => setNameValue(e.target.value)}
                        disabled={!isOwnerUser}
                    />
                </div>
                {isOwnerUser && (
                    <Button onClick={handleSaveName}>Save</Button>
                )}
            </TabsContent>

            <TabsContent value="parent" className="space-y-4 pt-4">
                <div className="space-y-2">
                    <Label>Move to</Label>
                    <div className="flex flex-col gap-2">
                        <Button
                            variant={parentId === null ? "default" : "outline"}
                            size="sm"
                            onClick={() => handleMove(null)}
                            disabled={!isOwnerUser}
                        >
                            Root
                        </Button>
                        {(store.foldersByParent["root"] ?? []).map((f) => (
                            <Button
                                key={f.id}
                                variant={
                                    parentId === f.id ? "default" : "outline"
                                }
                                size="sm"
                                onClick={() => handleMove(f.id)}
                                disabled={
                                    !isOwnerUser ||
                                    (resourceType === "folder" &&
                                        f.id === resourceId)
                                }
                            >
                                {f.name}
                            </Button>
                        ))}
                    </div>
                </div>
            </TabsContent>

            <TabsContent value="permissions" className="space-y-4 pt-4">
                {resourceType === "chat" ? (
                    <>
                        <div className="space-y-2">
                            <Label>People with access</Label>
                            <ScrollArea className="h-32 rounded-md border p-2">
                                {shares.length === 0 ? (
                                    <p className="text-muted-foreground text-sm">
                                        No shares yet.
                                    </p>
                                ) : (
                                    <ul className="space-y-1">
                                        {shares.map((s) => (
                                            <li
                                                key={s.subject}
                                                className="flex items-center justify-between text-sm"
                                            >
                                                <span>{s.subject}</span>
                                                <span className="text-muted-foreground">
                                                    {s.role}
                                                </span>
                                                {isOwnerUser && (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() =>
                                                            handleRemoveShare(
                                                                s.subject
                                                            )
                                                        }
                                                    >
                                                        Remove
                                                    </Button>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </ScrollArea>
                        </div>
                        {isOwnerUser && (
                            <div className="space-y-2">
                                <Label>Add person</Label>
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="Search by username"
                                        value={shareSearchQuery}
                                        onChange={(e) =>
                                            setShareSearchQuery(e.target.value)
                                        }
                                        onKeyDown={(e) =>
                                            e.key === "Enter" &&
                                            handleSearchUsers()
                                        }
                                    />
                                    <Button
                                        variant="outline"
                                        onClick={handleSearchUsers}
                                    >
                                        Search
                                    </Button>
                                </div>
                                {shareSearchResults.length > 0 && (
                                    <ul className="space-y-1 rounded-md border p-2">
                                        {shareSearchResults.map((u) => (
                                            <li
                                                key={u.id}
                                                className="flex items-center justify-between text-sm"
                                            >
                                                <span>{u.username}</span>
                                                <div className="flex gap-2">
                                                    <select
                                                        value={shareRole}
                                                        onChange={(e) =>
                                                            setShareRole(
                                                                e.target
                                                                    .value as
                                                                    | "viewer"
                                                                    | "editor"
                                                            )
                                                        }
                                                        className="rounded border px-2 py-1 text-sm"
                                                    >
                                                        <option value="viewer">
                                                            Viewer
                                                        </option>
                                                        <option value="editor">
                                                            Editor
                                                        </option>
                                                    </select>
                                                    <Button
                                                        size="sm"
                                                        onClick={() =>
                                                            handleAddShare(u.id)
                                                        }
                                                    >
                                                        Add
                                                    </Button>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}
                    </>
                ) : (
                    <p className="text-muted-foreground text-sm">
                        Folder-level sharing is not implemented. Permissions are
                        managed per chat—share individual chats from their
                        manage menu to grant access.
                    </p>
                )}
            </TabsContent>

            {resourceType === "folder" && (
                <TabsContent
                    value="systemPrompt"
                    className="space-y-4 pt-4"
                >
                    <div className="space-y-2">
                        <Label htmlFor="system-prompt">System prompt</Label>
                        <Textarea
                            id="system-prompt"
                            value={systemPromptValue}
                            onChange={(e) =>
                                setSystemPromptValue(e.target.value)
                            }
                            rows={6}
                            disabled={!isOwnerUser}
                            placeholder="Optional system prompt for chats in this folder..."
                        />
                    </div>
                    {isOwnerUser && (
                        <Button onClick={handleSaveSystemPrompt}>
                            Save
                        </Button>
                    )}
                </TabsContent>
            )}

            {isOwnerUser && (
                <TabsContent
                    value="destructive"
                    className="space-y-4 pt-4"
                >
                    <p className="text-muted-foreground text-sm">
                        {resourceType === "chat"
                            ? "Are you sure you want to delete this chat?"
                            : "Are you sure you want to delete this folder (and all its components)?"}
                    </p>
                    <Button
                        variant="destructive"
                        onClick={() => setDeleteConfirmOpen(true)}
                    >
                        <Trash2 className="mr-2 size-4" />
                        Delete
                    </Button>
                </TabsContent>
            )}
        </Tabs>
    );

    if (variant === "popup") {
        return (
            <>
                <Dialog open={open} onOpenChange={(o) => !o && onClose?.()}>
                    <DialogContent className="max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>
                                Manage {resourceType === "chat" ? "chat" : "folder"}
                            </DialogTitle>
                        </DialogHeader>
                        {content}
                    </DialogContent>
                </Dialog>
                <AlertDialog
                    open={deleteConfirmOpen}
                    onOpenChange={setDeleteConfirmOpen}
                >
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Confirm delete</AlertDialogTitle>
                            <AlertDialogDescription>
                                {resourceType === "chat"
                                    ? "Are you sure you want to delete this chat? This cannot be undone."
                                    : "Are you sure you want to delete this folder (and all its components)? Chats will move to root."}
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                onClick={handleDelete}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                                Delete
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </>
        );
    }

    return <div className="space-y-4">{content}</div>;
}
