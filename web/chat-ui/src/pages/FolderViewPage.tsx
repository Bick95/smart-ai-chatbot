"use client";

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
    ResourceManagement,
    type ResourceManagementTab,
} from "@/components/resource-management/ResourceManagement";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/auth";
import { useStatefulChatStore } from "@/stores/stateful-chat";
import { MoreHorizontal, MessageSquarePlus } from "lucide-react";

function isOwner(ownerSubject: string): boolean {
    const user = useAuthStore.getState().user;
    if (!user) return false;
    return ownerSubject === `user:${user.id}`;
}

export function FolderViewPage() {
    const { folderId } = useParams<{ folderId: string }>();
    const navigate = useNavigate();
    const [manageOpenForChat, setManageOpenForChat] = useState<{
        chatId: string;
        defaultTab: ResourceManagementTab;
    } | null>(null);

    const store = useStatefulChatStore();
    const folder = store.currentFolder;
    const folderChats = folderId
        ? store.folderChatsByFolderId[folderId] ?? { items: [], nextCursor: null }
        : { items: [], nextCursor: null };

    useEffect(() => {
        if (folderId) {
            store.loadFolder(folderId);
            store.loadChats(folderId);
        }
    }, [folderId, store]);

    const handleNewChatInFolder = () => {
        if (folderId) {
            navigate(`/chats?new=1&folderId=${folderId}`);
        }
    };

    if (!folderId) {
        return (
            <div className="flex flex-1 items-center justify-center p-8">
                <p className="text-muted-foreground">Invalid folder</p>
            </div>
        );
    }

    if (!folder && !store.isLoading) {
        return (
            <div className="flex flex-1 items-center justify-center p-8">
                <p className="text-muted-foreground">Folder not found</p>
            </div>
        );
    }

    return (
        <div className="flex min-h-0 flex-1 flex-col">
            <Tabs defaultValue="manage" className="flex min-h-0 flex-1 flex-col">
                <TabsList className="shrink-0">
                    <TabsTrigger value="manage">Manage</TabsTrigger>
                    <TabsTrigger value="chats">Chats</TabsTrigger>
                </TabsList>

                <TabsContent
                    value="manage"
                    className="min-h-0 flex-1 overflow-auto pt-4"
                >
                    <ResourceManagement
                        resourceType="folder"
                        resourceId={folderId}
                        resourceName={folder?.name}
                        variant="inline"
                    />
                </TabsContent>

                <TabsContent
                    value="chats"
                    className="min-h-0 flex-1 overflow-auto pt-4"
                >
                    <div className="space-y-4">
                        {isOwner(folder?.owner_subject ?? "") && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleNewChatInFolder}
                            >
                                <MessageSquarePlus className="mr-2 size-4" />
                                New chat in folder
                            </Button>
                        )}
                        <ul className="space-y-2">
                            {folderChats.items.map((chat) => (
                                <li
                                    key={chat.id}
                                    className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-4 py-2"
                                >
                                    <Link
                                        to={`/chats/${chat.id}`}
                                        className="min-w-0 flex-1 truncate font-medium hover:underline"
                                    >
                                        {chat.title || "Untitled chat"}
                                    </Link>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 shrink-0"
                                            >
                                                <MoreHorizontal className="size-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem
                                                onClick={() =>
                                                    setManageOpenForChat({
                                                        chatId: chat.id,
                                                        defaultTab:
                                                            "permissions",
                                                    })
                                                }
                                            >
                                                Share
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onClick={() =>
                                                    setManageOpenForChat({
                                                        chatId: chat.id,
                                                        defaultTab: "name",
                                                    })
                                                }
                                            >
                                                Rename
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onClick={() =>
                                                    setManageOpenForChat({
                                                        chatId: chat.id,
                                                        defaultTab: "parent",
                                                    })
                                                }
                                            >
                                                Move
                                            </DropdownMenuItem>
                                            {isOwner(chat.owner_subject) && (
                                                <DropdownMenuItem
                                                    onClick={() =>
                                                        setManageOpenForChat({
                                                            chatId: chat.id,
                                                            defaultTab:
                                                                "destructive",
                                                        })
                                                    }
                                                >
                                                    Delete
                                                </DropdownMenuItem>
                                            )}
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </li>
                            ))}
                        </ul>
                        {folderChats.items.length === 0 && (
                            <p className="text-muted-foreground py-8 text-center text-sm">
                                No chats in this folder yet.
                            </p>
                        )}
                        {folderChats.nextCursor && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                    store.loadChats(
                                        folderId,
                                        folderChats.nextCursor
                                    )
                                }
                            >
                                Load more
                            </Button>
                        )}
                    </div>
                </TabsContent>
            </Tabs>
            {manageOpenForChat && (
                <ResourceManagement
                    resourceType="chat"
                    resourceId={manageOpenForChat.chatId}
                    resourceName={
                        folderChats.items.find(
                            (c) => c.id === manageOpenForChat.chatId
                        )?.title ?? undefined
                    }
                    variant="popup"
                    defaultTab={manageOpenForChat.defaultTab}
                    open={true}
                    onClose={() => setManageOpenForChat(null)}
                    onUpdated={() => setManageOpenForChat(null)}
                />
            )}
        </div>
    );
}
