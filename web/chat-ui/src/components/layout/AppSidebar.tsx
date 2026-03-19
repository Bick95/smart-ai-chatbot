"use client";

import {
    LayoutDashboard,
    LogIn,
    LogOut,
    MessageSquare,
    MessageSquarePlus,
    Plus,
    UserPlus,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar";
import { useAuthStore } from "@/stores/auth";
import { useChatStore } from "@/stores/chat";
import { ChatsSidebar } from "./ChatsSidebar";

function StartNewChatButton() {
    const resetTemporaryChat = useChatStore((s) => s.resetTemporaryChat);
    return (
        <SidebarGroup>
            <SidebarGroupContent>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            onClick={() => resetTemporaryChat()}
                        >
                            <Plus className="size-4" />
                            <span>Start new chat</span>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarGroupContent>
        </SidebarGroup>
    );
}

export function AppSidebar() {
    const user = useAuthStore((s) => s.user);
    const clearAuth = useAuthStore((s) => s.clearAuth);
    const location = useLocation();

    const isOnChats =
        location.pathname.startsWith("/chats");
    const isOnTemporaryChat = location.pathname === "/chat";

    const navItems = [
        { to: "/chat", icon: MessageSquare, label: "Temporary Chat" },
        { to: "/chats", icon: MessageSquarePlus, label: "Chats" },
        { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    ];

    return (
        <Sidebar collapsible="icon">
            <SidebarHeader className="border-b border-sidebar-border">
                <div className="flex h-14 items-center gap-2 px-4">
                    <span className="font-semibold">Chatbot</span>
                </div>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {navItems.map(({ to, icon: Icon, label }) => (
                                <SidebarMenuItem key={to}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={
                                            location.pathname === to ||
                                            (to === "/chats" &&
                                                location.pathname.startsWith(
                                                    "/chats"
                                                ))
                                        }
                                    >
                                        <Link to={to}>
                                            <Icon className="size-4" />
                                            <span>{label}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
                {isOnChats && (
                    <ChatsSidebar />
                )}
                {isOnTemporaryChat && (
                    <StartNewChatButton />
                )}
            </SidebarContent>

            <SidebarFooter className="border-t border-sidebar-border">
                <SidebarMenu>
                    {user ? (
                        <SidebarMenuItem>
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <SidebarMenuButton
                                        size="lg"
                                        className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                                    >
                                        <Avatar className="size-8">
                                            <AvatarFallback className="bg-primary/10 text-primary text-sm font-medium">
                                                {user.username
                                                    .slice(0, 2)
                                                    .toUpperCase()}
                                            </AvatarFallback>
                                        </Avatar>
                                        <div className="grid flex-1 text-left text-sm leading-tight">
                                            <span className="truncate font-medium">
                                                {user.username}
                                            </span>
                                            <span className="text-muted-foreground truncate text-xs">
                                                {user.email}
                                            </span>
                                        </div>
                                    </SidebarMenuButton>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                    className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                                    side="top"
                                    align="start"
                                    sideOffset={4}
                                >
                                    <DropdownMenuLabel className="font-normal">
                                        <div className="flex flex-col space-y-1">
                                            <p className="text-sm font-medium leading-none">
                                                {user.username}
                                            </p>
                                            <p className="text-muted-foreground text-xs leading-none">
                                                {user.email}
                                            </p>
                                        </div>
                                    </DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        variant="destructive"
                                        onClick={() => clearAuth()}
                                    >
                                        <LogOut className="size-4" />
                                        Sign out
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </SidebarMenuItem>
                    ) : (
                        <>
                            <SidebarMenuItem>
                                <SidebarMenuButton asChild>
                                    <Link to="/login">
                                        <LogIn className="size-4" />
                                        <span>Sign in</span>
                                    </Link>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                            <SidebarMenuItem>
                                <SidebarMenuButton asChild>
                                    <Link to="/signup">
                                        <UserPlus className="size-4" />
                                        <span>Sign up</span>
                                    </Link>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </>
                    )}
                </SidebarMenu>
            </SidebarFooter>
        </Sidebar>
    );
}
