"""In-memory mock chat adapter for testing (no DB required)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

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


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MockChatAdapter:
    """In-memory chat adapter for tests. Implements ChatPort."""

    def __init__(self) -> None:
        self._chats: dict[str, Chat] = {}
        self._messages: dict[str, list[ChatMessage]] = {}  # chat_id -> messages
        self._permissions: dict[tuple[str, str], ChatShare] = {}  # (chat_id, subject)
        self._folders: dict[str, Folder] = {}

    def _has_access(
        self, chat_id: str, subject: Subject, *, need_edit: bool = False
    ) -> bool:
        chat = self._chats.get(chat_id)
        if chat is None:
            return False
        if chat.owner_subject == subject.to_str():
            return True
        key = (chat_id, subject.to_str())
        share = self._permissions.get(key)
        if share is None:
            return False
        if need_edit:
            return share.role == ShareRole.EDITOR
        return True

    async def create_chat(
        self,
        subject: Subject,
        *,
        folder_id: str | None = None,
        title: str | None = None,
    ) -> Chat:
        chat_id = str(uuid4())
        now = _now()
        chat = Chat(
            id=chat_id,
            owner_subject=subject.to_str(),
            folder_id=folder_id,
            title=title.strip() if title else None,
            created_at=now,
            updated_at=now,
        )
        self._chats[chat_id] = chat
        self._messages[chat_id] = []
        return chat

    async def get_chat(self, chat_id: str, subject: Subject) -> Chat | None:
        chat = self._chats.get(chat_id)
        if chat is None:
            return None
        if not self._has_access(chat_id, subject):
            return None
        return chat

    async def list_chats(
        self,
        subject: Subject,
        *,
        folder_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[Chat]:
        accessible = [
            c for c in self._chats.values()
            if self._has_access(c.id, subject)
            and (folder_id is None or c.folder_id == folder_id)
        ]
        accessible.sort(key=lambda c: (c.updated_at, c.id), reverse=True)

        start = 0
        if cursor:
            for i, c in enumerate(accessible):
                if c.id == cursor:
                    start = i + 1
                    break
            else:
                start = len(accessible)

        page = accessible[start : start + limit + 1]
        items = page[:limit]
        next_cursor = page[limit].id if len(page) > limit else None
        return PaginatedResult(items=items, next_cursor=next_cursor)

    async def add_message(
        self, chat_id: str, subject: Subject, role: MessageRole, content: str
    ) -> ChatMessage:
        if not self._has_access(chat_id, subject, need_edit=True):
            raise PermissionError("No edit access")
        chat = self._chats.get(chat_id)
        if chat is None:
            raise ValueError("Chat not found")
        msg_id = str(uuid4())
        now = _now()
        msg = ChatMessage(
            id=msg_id,
            chat_id=chat_id,
            role=role,
            content=content,
            created_at=now,
        )
        self._messages[chat_id].append(msg)
        self._chats[chat_id] = Chat(
            id=chat.id,
            owner_subject=chat.owner_subject,
            folder_id=chat.folder_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=now,
        )
        return msg

    async def get_messages(
        self,
        chat_id: str,
        subject: Subject,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[ChatMessage]:
        if not self._has_access(chat_id, subject):
            return PaginatedResult(items=[], next_cursor=None)
        msgs = self._messages.get(chat_id, [])
        msgs = sorted(msgs, key=lambda m: (m.created_at, m.id))

        start = 0
        if cursor:
            for i, m in enumerate(msgs):
                if m.id == cursor:
                    start = i + 1
                    break
            else:
                start = len(msgs)

        page = msgs[start : start + limit + 1]
        items = page[:limit]
        next_cursor = page[limit].id if len(page) > limit else None
        return PaginatedResult(items=items, next_cursor=next_cursor)

    async def update_chat(
        self,
        chat_id: str,
        subject: Subject,
        *,
        title: str | None = None,
        folder_id: str | None = None,
        update_title: bool = False,
        update_folder: bool = False,
    ) -> Chat | None:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != subject.to_str():
            return None
        if not update_title and not update_folder:
            return chat
        now = _now()
        new_title = title.strip() if title else None if update_title else chat.title
        new_folder_id = folder_id if update_folder else chat.folder_id
        updated = Chat(
            id=chat.id,
            owner_subject=chat.owner_subject,
            folder_id=new_folder_id,
            title=new_title,
            created_at=chat.created_at,
            updated_at=now,
        )
        self._chats[chat_id] = updated
        return updated

    async def delete_chat(self, chat_id: str, subject: Subject) -> bool:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != subject.to_str():
            return False
        del self._chats[chat_id]
        self._messages.pop(chat_id, None)
        for (cid, subj) in list(self._permissions.keys()):
            if cid == chat_id:
                del self._permissions[(cid, subj)]
        return True

    async def add_share(
        self, chat_id: str, owner: Subject, grantee: Subject, role: ShareRole
    ) -> ChatShare:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != owner.to_str():
            raise PermissionError("Not owner")
        now = _now()
        grantee_str = grantee.to_str()
        share = ChatShare(
            chat_id=chat_id,
            subject=grantee_str,
            role=role,
            created_at=now,
        )
        self._permissions[(chat_id, grantee_str)] = share
        return share

    async def remove_share(
        self, chat_id: str, owner: Subject, grantee: Subject
    ) -> bool:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != owner.to_str():
            return False
        key = (chat_id, grantee.to_str())
        if key in self._permissions:
            del self._permissions[key]
            return True
        return False

    async def list_shares(self, chat_id: str, owner: Subject) -> list[ChatShare]:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != owner.to_str():
            return []
        return [
            s for (cid, _), s in self._permissions.items()
            if cid == chat_id
        ]

    async def get_folder(
        self, folder_id: str, subject: Subject
    ) -> Folder | None:
        folder = self._folders.get(folder_id)
        if folder is None:
            return None
        if folder.owner_subject != subject.to_str():
            return None
        if not self._has_folder_access(folder_id, subject):
            return None
        return folder

    def _has_folder_access(self, folder_id: str, subject: Subject) -> bool:
        """Check if subject can access folder (owner or has access via shared chat)."""
        folder = self._folders.get(folder_id)
        if folder is None:
            return False
        if folder.owner_subject == subject.to_str():
            return True
        for chat in self._chats.values():
            if chat.folder_id == folder_id and self._has_access(chat.id, subject):
                return True
        return False

    async def list_folders(
        self, subject: Subject, *, parent_id: str | None = None
    ) -> list[Folder]:
        folders = [
            f for f in self._folders.values()
            if f.parent_id == parent_id and self._has_folder_access(f.id, subject)
        ]
        return sorted(folders, key=lambda f: f.name)

    async def create_folder(
        self,
        subject: Subject,
        name: str,
        *,
        parent_id: str | None = None,
        system_prompt: str | None = None,
    ) -> Folder:
        folder_id = str(uuid4())
        now = _now()
        folder = Folder(
            id=folder_id,
            owner_subject=subject.to_str(),
            parent_id=parent_id,
            name=name.strip(),
            system_prompt=system_prompt.strip() if system_prompt else None,
            created_at=now,
            updated_at=now,
        )
        self._folders[folder_id] = folder
        return folder

    async def rename_folder(
        self, folder_id: str, subject: Subject, name: str
    ) -> Folder | None:
        folder = self._folders.get(folder_id)
        if folder is None or folder.owner_subject != subject.to_str():
            return None
        now = _now()
        updated = Folder(
            id=folder.id,
            owner_subject=folder.owner_subject,
            parent_id=folder.parent_id,
            name=name.strip(),
            system_prompt=folder.system_prompt,
            created_at=folder.created_at,
            updated_at=now,
        )
        self._folders[folder_id] = updated
        return updated

    def _is_descendant(self, node_id: str, ancestor_id: str) -> bool:
        """Check if node_id is a descendant of ancestor_id (walk up from node)."""
        current = self._folders.get(node_id)
        while current:
            if current.id == ancestor_id:
                return True
            current = self._folders.get(current.parent_id) if current.parent_id else None
        return False

    async def move_folder_to_parent(
        self, folder_id: str, subject: Subject, parent_id: str | None
    ) -> Folder | None:
        folder = self._folders.get(folder_id)
        if folder is None or folder.owner_subject != subject.to_str():
            return None
        if parent_id is not None:
            if parent_id == folder_id:
                return None  # Cannot move into self
            if self._is_descendant(parent_id, folder_id):
                return None  # Would create cycle
        now = _now()
        updated = Folder(
            id=folder.id,
            owner_subject=folder.owner_subject,
            parent_id=parent_id,
            name=folder.name,
            system_prompt=folder.system_prompt,
            created_at=folder.created_at,
            updated_at=now,
        )
        self._folders[folder_id] = updated
        return updated

    async def delete_folder(self, folder_id: str, subject: Subject) -> bool:
        folder = self._folders.get(folder_id)
        if folder is None or folder.owner_subject != subject.to_str():
            return False
        del self._folders[folder_id]
        for chat in self._chats.values():
            if chat.folder_id == folder_id:
                self._chats[chat.id] = Chat(
                    id=chat.id,
                    owner_subject=chat.owner_subject,
                    folder_id=None,
                    title=chat.title,
                    created_at=chat.created_at,
                    updated_at=_now(),
                )
        for fid, f in list(self._folders.items()):
            if f.parent_id == folder_id:
                self._folders[fid] = Folder(
                    id=f.id,
                    owner_subject=f.owner_subject,
                    parent_id=folder.parent_id,
                    name=f.name,
                    system_prompt=f.system_prompt,
                    created_at=f.created_at,
                    updated_at=_now(),
                )
        return True

    async def move_chat_to_folder(
        self, chat_id: str, subject: Subject, folder_id: str | None
    ) -> bool:
        chat = self._chats.get(chat_id)
        if chat is None or chat.owner_subject != subject.to_str():
            return False
        self._chats[chat_id] = Chat(
            id=chat.id,
            owner_subject=chat.owner_subject,
            folder_id=folder_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=_now(),
        )
        return True
