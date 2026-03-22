"""Chat port (interface) for the hexagonal architecture."""

from __future__ import annotations

from typing import Protocol

from src.app_data.ports.types import (
    Chat,
    ChatMessage,
    ChatShare,
    Folder,
    MessageRole,
    PaginatedResult,
    ShareRole,
    Subject,
)
from src.utils.validation import Uuid4Str


class ChatPort(Protocol):
    """Port for chat and folder persistence operations."""

    async def create_chat(
        self,
        subject: Subject,
        *,
        folder_id: Uuid4Str | None = None,
        title: str | None = None,
    ) -> Chat:
        """Create a new chat. Returns the created Chat.
        System prompt is NOT stored; it is fetched from the folder on each request."""
        ...

    async def get_chat(self, chat_id: Uuid4Str, subject: Subject) -> Chat | None:
        """Get chat if subject has access (owner or shared). Returns None if not found or no access."""
        ...

    async def list_chats(
        self,
        subject: Subject,
        *,
        folder_id: Uuid4Str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[Chat]:
        """List chats subject owns or has access to. Optionally filter by folder. Paginated."""
        ...

    async def list_chats_shared_with_me(
        self,
        subject: Subject,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[Chat]:
        """List chats shared with the subject (access granted but not owner). Flat list; no folder filter."""
        ...

    async def add_message(
        self, chat_id: Uuid4Str, subject: Subject, role: MessageRole, content: str
    ) -> ChatMessage:
        """Append a message. Requires editor or owner permission."""
        ...

    async def get_messages(
        self,
        chat_id: Uuid4Str,
        subject: Subject,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[ChatMessage]:
        """Get messages. Requires viewer, editor, or owner. Paginated."""
        ...

    async def update_chat(
        self,
        chat_id: Uuid4Str,
        subject: Subject,
        *,
        title: str | None = None,
        folder_id: Uuid4Str | None = None,
        update_title: bool = False,
        update_folder: bool = False,
    ) -> Chat | None:
        """Update chat (title and/or folder). Owner only.
        update_title/update_folder flags indicate which fields to update."""
        ...

    async def delete_chat(self, chat_id: Uuid4Str, subject: Subject) -> bool:
        """Delete chat. Owner only. Returns True if deleted."""
        ...

    async def add_share(
        self, chat_id: Uuid4Str, owner: Subject, grantee: Subject, role: ShareRole
    ) -> ChatShare:
        """Share chat with grantee. Owner only."""
        ...

    async def remove_share(
        self, chat_id: Uuid4Str, owner: Subject, grantee: Subject
    ) -> bool:
        """Revoke share. Owner only. Returns True if removed."""
        ...

    async def list_shares(self, chat_id: Uuid4Str, owner: Subject) -> list[ChatShare]:
        """List shares for a chat. Owner only."""
        ...

    async def get_folder(
        self, folder_id: Uuid4Str, subject: Subject
    ) -> Folder | None:
        """Get folder if subject has access. Returns None if not found or no access."""
        ...

    async def list_folders(
        self, subject: Subject, *, parent_id: Uuid4Str | None = None
    ) -> list[Folder]:
        """List folders. parent_id=None for root folders."""
        ...

    async def create_folder(
        self,
        subject: Subject,
        name: str,
        *,
        parent_id: Uuid4Str | None = None,
        system_prompt: str | None = None,
    ) -> Folder:
        """Create a folder."""
        ...

    async def rename_folder(
        self, folder_id: Uuid4Str, subject: Subject, name: str
    ) -> Folder | None:
        """Rename folder. Owner only. Returns updated Folder or None."""
        ...

    async def update_folder(
        self, folder_id: Uuid4Str, subject: Subject, **kwargs: str | None
    ) -> Folder | None:
        """Update folder (name and/or system_prompt). Owner only.
        Pass name=..., system_prompt=... for fields to update. system_prompt=None clears it."""
        ...

    async def move_folder_to_parent(
        self, folder_id: Uuid4Str, subject: Subject, parent_id: Uuid4Str | None
    ) -> Folder | None:
        """Move folder to another parent. parent_id=None moves to root. Owner only.
        Rejects moving into self or into a descendant (would create cycle)."""
        ...

    async def delete_folder(self, folder_id: Uuid4Str, subject: Subject) -> bool:
        """Delete folder. Chats move to parent or root. Owner only. Returns True if deleted."""
        ...

    async def move_chat_to_folder(
        self, chat_id: Uuid4Str, subject: Subject, folder_id: Uuid4Str | None
    ) -> bool:
        """Move chat to folder. folder_id=None moves to root. Owner only."""
        ...
