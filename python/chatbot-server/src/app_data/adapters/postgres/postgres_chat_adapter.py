"""Postgres chat adapter: stores chats, messages, folders with RLS."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import UUID

import asyncpg

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


def _parse_ts(value: object) -> datetime:
    """Parse timestamp from DB to timezone-aware datetime."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def _decode_cursor_chat(cursor: str | None) -> tuple[datetime, str] | None:
    """Decode cursor for list_chats: 'timestamp|id'."""
    if not cursor or not isinstance(cursor, str) or "|" not in cursor:
        return None
    parts = cursor.split("|", 1)
    if len(parts) != 2:
        return None
    try:
        ts = datetime.fromisoformat(parts[0].replace("Z", "+00:00"))
        return (ts, parts[1])
    except (ValueError, TypeError):
        return None


def _encode_cursor_chat(updated_at: datetime, id_: str) -> str:
    return f"{updated_at.isoformat()}|{id_}"


def _decode_cursor_message(cursor: str | None) -> tuple[datetime, str] | None:
    """Decode cursor for get_messages: 'timestamp|id'."""
    return _decode_cursor_chat(cursor)


def _encode_cursor_message(created_at: datetime, id_: str) -> str:
    return f"{created_at.isoformat()}|{id_}"


@asynccontextmanager
async def _conn_with_subject(
    pool: asyncpg.Pool, subject: Subject
) -> AsyncIterator[asyncpg.Connection]:
    """Acquire connection and set RLS session variables."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SET LOCAL app.current_subject = $1",
                subject.to_str(),
            )
            yield conn


class PostgresChatAdapter:
    """Chat adapter using Postgres with RLS for RBAC."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_chat(
        self,
        subject: Subject,
        *,
        folder_id: str | None = None,
        title: str | None = None,
    ) -> Chat:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO chats (owner_subject, folder_id, title)
                VALUES ($1, $2, $3)
                RETURNING id, owner_subject, folder_id, title, created_at, updated_at
                """,
                subject.to_str(),
                UUID(folder_id) if folder_id else None,
                title.strip() if title else None,
            )
        return _row_to_chat(row)

    async def get_chat(self, chat_id: str, subject: Subject) -> Chat | None:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                SELECT id, owner_subject, folder_id, title, created_at, updated_at
                FROM chats
                WHERE id = $1
                """,
                UUID(chat_id),
            )
        if row is None:
            return None
        return _row_to_chat(row)

    async def list_chats(
        self,
        subject: Subject,
        *,
        folder_id: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[Chat]:
        async with _conn_with_subject(self._pool, subject) as conn:
            decoded = _decode_cursor_chat(cursor)
            if decoded:
                cursor_ts, cursor_id = decoded
                if folder_id is not None:
                    rows = await conn.fetch(
                        """
                        SELECT id, owner_subject, folder_id, title, created_at, updated_at
                        FROM chats
                        WHERE folder_id = $1
                        AND (updated_at, id) < ($2, $3)
                        ORDER BY updated_at DESC, id DESC
                        LIMIT $4
                        """,
                        UUID(folder_id),
                        cursor_ts,
                        UUID(cursor_id),
                        limit + 1,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, owner_subject, folder_id, title, created_at, updated_at
                        FROM chats
                        WHERE (updated_at, id) < ($1, $2)
                        ORDER BY updated_at DESC, id DESC
                        LIMIT $3
                        """,
                        cursor_ts,
                        UUID(cursor_id),
                        limit + 1,
                    )
            else:
                if folder_id is not None:
                    rows = await conn.fetch(
                        """
                        SELECT id, owner_subject, folder_id, title, created_at, updated_at
                        FROM chats
                        WHERE folder_id = $1
                        ORDER BY updated_at DESC, id DESC
                        LIMIT $2
                        """,
                        UUID(folder_id),
                        limit + 1,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, owner_subject, folder_id, title, created_at, updated_at
                        FROM chats
                        ORDER BY updated_at DESC, id DESC
                        LIMIT $1
                        """,
                        limit + 1,
                    )

        items = [_row_to_chat(r) for r in rows[:limit]]
        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = _encode_cursor_chat(
                _parse_ts(last["updated_at"]), str(last["id"])
            )
        return PaginatedResult(items=items, next_cursor=next_cursor)

    async def add_message(
        self, chat_id: str, subject: Subject, role: MessageRole, content: str
    ) -> ChatMessage:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO chat_messages (chat_id, role, content)
                VALUES ($1, $2, $3)
                RETURNING id, chat_id, role, content, created_at
                """,
                UUID(chat_id),
                role,
                content,
            )
            await conn.execute(
                "UPDATE chats SET updated_at = NOW() WHERE id = $1",
                UUID(chat_id),
            )
        return _row_to_message(row)

    async def get_messages(
        self,
        chat_id: str,
        subject: Subject,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> PaginatedResult[ChatMessage]:
        async with _conn_with_subject(self._pool, subject) as conn:
            decoded = _decode_cursor_message(cursor)
            if decoded:
                cursor_ts, cursor_id = decoded
                rows = await conn.fetch(
                    """
                    SELECT id, chat_id, role, content, created_at
                    FROM chat_messages
                    WHERE chat_id = $1
                    AND (created_at, id) > ($2, $3)
                    ORDER BY created_at ASC, id ASC
                    LIMIT $4
                    """,
                    UUID(chat_id),
                    cursor_ts,
                    UUID(cursor_id),
                    limit + 1,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, chat_id, role, content, created_at
                    FROM chat_messages
                    WHERE chat_id = $1
                    ORDER BY created_at ASC, id ASC
                    LIMIT $2
                    """,
                    UUID(chat_id),
                    limit + 1,
                )

        items = [_row_to_message(r) for r in rows[:limit]]
        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = _encode_cursor_message(
                _parse_ts(last["created_at"]), str(last["id"])
            )
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
        if not update_title and not update_folder:
            return await self.get_chat(chat_id, subject)
        sets = ["updated_at = NOW()"]
        args: list = []
        n = 1
        if update_title:
            sets.append(f"title = ${n}")
            args.append(title.strip() if title else None)
            n += 1
        if update_folder:
            sets.append(f"folder_id = ${n}")
            args.append(UUID(folder_id) if folder_id else None)
            n += 1
        args.append(UUID(chat_id))
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                f"""
                UPDATE chats
                SET {", ".join(sets)}
                WHERE id = ${n}
                RETURNING id, owner_subject, folder_id, title, created_at, updated_at
                """,
                *args,
            )
        if row is None:
            return None
        return _row_to_chat(row)

    async def delete_chat(self, chat_id: str, subject: Subject) -> bool:
        async with _conn_with_subject(self._pool, subject) as conn:
            result = await conn.execute(
                "DELETE FROM chats WHERE id = $1",
                UUID(chat_id),
            )
        return result == "DELETE 1"

    async def add_share(
        self, chat_id: str, owner: Subject, grantee: Subject, role: ShareRole
    ) -> ChatShare:
        async with _conn_with_subject(self._pool, owner) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO chat_permissions (chat_id, subject, role)
                VALUES ($1, $2, $3)
                RETURNING chat_id, subject, role, created_at
                """,
                UUID(chat_id),
                grantee.to_str(),
                role,
            )
        return _row_to_share(row)

    async def remove_share(
        self, chat_id: str, owner: Subject, grantee: Subject
    ) -> bool:
        async with _conn_with_subject(self._pool, owner) as conn:
            result = await conn.execute(
                """
                DELETE FROM chat_permissions
                WHERE chat_id = $1 AND subject = $2
                """,
                UUID(chat_id),
                grantee.to_str(),
            )
        return result == "DELETE 1"

    async def list_shares(self, chat_id: str, owner: Subject) -> list[ChatShare]:
        async with _conn_with_subject(self._pool, owner) as conn:
            rows = await conn.fetch(
                """
                SELECT chat_id, subject, role, created_at
                FROM chat_permissions
                WHERE chat_id = $1
                """,
                UUID(chat_id),
            )
        return [_row_to_share(r) for r in rows]

    async def get_folder(
        self, folder_id: str, subject: Subject
    ) -> Folder | None:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                SELECT id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                FROM chat_folders
                WHERE id = $1
                """,
                UUID(folder_id),
            )
        if row is None:
            return None
        return _row_to_folder(row)

    async def list_folders(
        self, subject: Subject, *, parent_id: str | None = None
    ) -> list[Folder]:
        async with _conn_with_subject(self._pool, subject) as conn:
            if parent_id is not None:
                rows = await conn.fetch(
                    """
                    SELECT id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                    FROM chat_folders
                    WHERE parent_id = $1
                    ORDER BY name
                    """,
                    UUID(parent_id),
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                    FROM chat_folders
                    WHERE parent_id IS NULL
                    ORDER BY name
                    """,
                )
        return [_row_to_folder(r) for r in rows]

    async def create_folder(
        self,
        subject: Subject,
        name: str,
        *,
        parent_id: str | None = None,
        system_prompt: str | None = None,
    ) -> Folder:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO chat_folders (owner_subject, parent_id, name, system_prompt)
                VALUES ($1, $2, $3, $4)
                RETURNING id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                """,
                subject.to_str(),
                UUID(parent_id) if parent_id else None,
                name.strip(),
                system_prompt.strip() if system_prompt else None,
            )
        return _row_to_folder(row)

    async def rename_folder(
        self, folder_id: str, subject: Subject, name: str
    ) -> Folder | None:
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                UPDATE chat_folders
                SET name = $1, updated_at = NOW()
                WHERE id = $2
                RETURNING id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                """,
                name.strip(),
                UUID(folder_id),
            )
        if row is None:
            return None
        return _row_to_folder(row)

    async def update_folder(
        self, folder_id: str, subject: Subject, **kwargs: str | None
    ) -> Folder | None:
        if not kwargs:
            return await self.get_folder(folder_id, subject)
        updates = []
        values = []
        idx = 1
        if "name" in kwargs:
            updates.append(f"name = ${idx}")
            values.append(kwargs["name"].strip() if kwargs["name"] else None)
            idx += 1
        if "system_prompt" in kwargs:
            updates.append(f"system_prompt = ${idx}")
            values.append(
                kwargs["system_prompt"].strip()
                if kwargs["system_prompt"]
                else None
            )
            idx += 1
        if not updates:
            return await self.get_folder(folder_id, subject)
        updates.append("updated_at = NOW()")
        values.append(UUID(folder_id))
        query = f"""
            UPDATE chat_folders
            SET {", ".join(updates)}
            WHERE id = ${idx}
            RETURNING id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
        """
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(query, *values)
        if row is None:
            return None
        return _row_to_folder(row)

    async def move_folder_to_parent(
        self, folder_id: str, subject: Subject, parent_id: str | None
    ) -> Folder | None:
        folder_uuid = UUID(folder_id)
        if parent_id is not None:
            parent_uuid = UUID(parent_id)
            if folder_uuid == parent_uuid:
                return None  # Cannot move into self
            async with _conn_with_subject(self._pool, subject) as conn:
                # Check parent is not a descendant (would create cycle)
                descendant = await conn.fetchval(
                    """
                    WITH RECURSIVE descendants AS (
                        SELECT id FROM chat_folders WHERE id = $1
                        UNION ALL
                        SELECT cf.id FROM chat_folders cf
                        JOIN descendants d ON cf.parent_id = d.id
                    )
                    SELECT 1 FROM descendants WHERE id = $2
                    """,
                    folder_uuid,
                    parent_uuid,
                )
                if descendant is not None:
                    return None  # Would create cycle
        async with _conn_with_subject(self._pool, subject) as conn:
            row = await conn.fetchrow(
                """
                UPDATE chat_folders
                SET parent_id = $1, updated_at = NOW()
                WHERE id = $2
                RETURNING id, owner_subject, parent_id, name, system_prompt, created_at, updated_at
                """,
                parent_uuid if parent_id else None,
                folder_uuid,
            )
        if row is None:
            return None
        return _row_to_folder(row)

    async def delete_folder(self, folder_id: str, subject: Subject) -> bool:
        async with _conn_with_subject(self._pool, subject) as conn:
            result = await conn.execute(
                "DELETE FROM chat_folders WHERE id = $1",
                UUID(folder_id),
            )
        return result == "DELETE 1"

    async def move_chat_to_folder(
        self, chat_id: str, subject: Subject, folder_id: str | None
    ) -> bool:
        async with _conn_with_subject(self._pool, subject) as conn:
            result = await conn.execute(
                """
                UPDATE chats
                SET folder_id = $1, updated_at = NOW()
                WHERE id = $2
                """,
                UUID(folder_id) if folder_id else None,
                UUID(chat_id),
            )
        return result == "UPDATE 1"


def _row_to_chat(row: asyncpg.Record) -> Chat:
    return Chat(
        id=str(row["id"]),
        owner_subject=row["owner_subject"],
        folder_id=str(row["folder_id"]) if row["folder_id"] else None,
        title=row["title"] if row.get("title") else None,
        created_at=_parse_ts(row["created_at"]),
        updated_at=_parse_ts(row["updated_at"]),
    )


def _row_to_message(row: asyncpg.Record) -> ChatMessage:
    return ChatMessage(
        id=str(row["id"]),
        chat_id=str(row["chat_id"]),
        role=row["role"],
        content=row["content"],
        created_at=_parse_ts(row["created_at"]),
    )


def _row_to_share(row: asyncpg.Record) -> ChatShare:
    return ChatShare(
        chat_id=str(row["chat_id"]),
        subject=row["subject"],
        role=row["role"],
        created_at=_parse_ts(row["created_at"]),
    )


def _row_to_folder(row: asyncpg.Record) -> Folder:
    return Folder(
        id=str(row["id"]),
        owner_subject=row["owner_subject"],
        parent_id=str(row["parent_id"]) if row["parent_id"] else None,
        name=row["name"],
        system_prompt=row.get("system_prompt"),
        created_at=_parse_ts(row["created_at"]),
        updated_at=_parse_ts(row["updated_at"]),
    )
