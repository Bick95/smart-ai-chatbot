"""Unit tests for mock chat adapter."""

import pytest

from src.app_data.adapters.mock.mock_chat_adapter import MockChatAdapter
from src.app_data.ports.types import Subject, SubjectType


@pytest.mark.unit
class TestMockChatAdapter:
    """Direct unit tests for MockChatAdapter."""

    @pytest.fixture
    def adapter(self) -> MockChatAdapter:
        return MockChatAdapter()

    @pytest.fixture
    def subject(self) -> Subject:
        return Subject(
            subject_type=SubjectType.USER,
            subject_id="550e8400-e29b-41d4-a716-446655440000",
        )

    @pytest.mark.asyncio
    async def test_create_chat(self, adapter: MockChatAdapter, subject: Subject):
        """create_chat returns chat with id and owner."""
        chat = await adapter.create_chat(subject, title="My Chat")
        assert chat.id
        assert chat.owner_subject == subject.to_str()
        assert chat.title == "My Chat"
        assert chat.folder_id is None

    @pytest.mark.asyncio
    async def test_create_chat_in_folder(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """create_chat with folder_id stores folder."""
        folder = await adapter.create_folder(subject, name="Folder")
        chat = await adapter.create_chat(subject, folder_id=folder.id)
        assert chat.folder_id == folder.id

    @pytest.mark.asyncio
    async def test_get_chat_returns_chat(self, adapter: MockChatAdapter, subject: Subject):
        """get_chat returns chat when found and user has access."""
        created = await adapter.create_chat(subject, title="Test")
        found = await adapter.get_chat(created.id, subject)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_chat_returns_none_for_unknown(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """get_chat returns None for unknown chat."""
        found = await adapter.get_chat("550e8400-e29b-41d4-a716-446655440000", subject)
        assert found is None

    @pytest.mark.asyncio
    async def test_list_chats_returns_owned(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """list_chats returns chats owned by subject."""
        await adapter.create_chat(subject, title="C1")
        await adapter.create_chat(subject, title="C2")
        result = await adapter.list_chats(subject)
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_add_message(self, adapter: MockChatAdapter, subject: Subject):
        """add_message appends message to chat."""
        chat = await adapter.create_chat(subject, title="Chat")
        msg = await adapter.add_message(
            chat.id, subject, role="user", content="Hello"
        )
        assert msg.chat_id == chat.id
        assert msg.role == "user"
        assert msg.content == "Hello"
        msgs = await adapter.get_messages(chat.id, subject)
        assert len(msgs.items) == 1
        assert msgs.items[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_create_folder(self, adapter: MockChatAdapter, subject: Subject):
        """create_folder returns folder with id."""
        folder = await adapter.create_folder(subject, name="My Folder")
        assert folder.id
        assert folder.name == "My Folder"
        assert folder.parent_id is None

    @pytest.mark.asyncio
    async def test_create_folder_with_parent(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """create_folder with parent_id stores parent."""
        parent = await adapter.create_folder(subject, name="Parent")
        child = await adapter.create_folder(
            subject, name="Child", parent_id=parent.id
        )
        assert child.parent_id == parent.id

    @pytest.mark.asyncio
    async def test_list_folders(self, adapter: MockChatAdapter, subject: Subject):
        """list_folders returns folders for subject."""
        await adapter.create_folder(subject, name="F1")
        await adapter.create_folder(subject, name="F2")
        folders = await adapter.list_folders(subject, parent_id=None)
        assert len(folders) == 2

    @pytest.mark.asyncio
    async def test_update_chat_title(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """update_chat updates title."""
        chat = await adapter.create_chat(subject, title="Old")
        updated = await adapter.update_chat(
            chat.id, subject, title="New", update_title=True
        )
        assert updated is not None
        assert updated.title == "New"

    @pytest.mark.asyncio
    async def test_delete_chat(self, adapter: MockChatAdapter, subject: Subject):
        """delete_chat removes chat."""
        chat = await adapter.create_chat(subject, title="To Delete")
        ok = await adapter.delete_chat(chat.id, subject)
        assert ok is True
        found = await adapter.get_chat(chat.id, subject)
        assert found is None

    @pytest.mark.asyncio
    async def test_add_and_remove_share(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """add_share and remove_share work for owner."""
        from src.app_data.ports.types import ShareRole

        chat = await adapter.create_chat(subject, title="Shared")
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        share = await adapter.add_share(chat.id, subject, grantee, ShareRole.VIEWER)
        assert share.chat_id == chat.id
        assert share.subject == grantee.to_str()
        assert share.role == ShareRole.VIEWER
        shares = await adapter.list_shares(chat.id, subject)
        assert len(shares) == 1
        ok = await adapter.remove_share(chat.id, subject, grantee)
        assert ok is True
        shares = await adapter.list_shares(chat.id, subject)
        assert len(shares) == 0

    @pytest.mark.asyncio
    async def test_get_folder(self, adapter: MockChatAdapter, subject: Subject):
        """get_folder returns folder when found."""
        folder = await adapter.create_folder(subject, name="Test Folder")
        found = await adapter.get_folder(folder.id, subject)
        assert found is not None
        assert found.name == "Test Folder"

    @pytest.mark.asyncio
    async def test_update_folder(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """update_folder updates name and system_prompt."""
        folder = await adapter.create_folder(subject, name="Original")
        updated = await adapter.update_folder(
            folder.id, subject, name="Updated", system_prompt="Be helpful."
        )
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.system_prompt == "Be helpful."

    @pytest.mark.asyncio
    async def test_move_chat_to_folder(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """move_chat_to_folder moves chat into folder."""
        chat = await adapter.create_chat(subject, title="Chat")
        folder = await adapter.create_folder(subject, name="Dest")
        ok = await adapter.move_chat_to_folder(chat.id, subject, folder.id)
        assert ok is True
        found = await adapter.get_chat(chat.id, subject)
        assert found is not None
        assert found.folder_id == folder.id

    @pytest.mark.asyncio
    async def test_list_chats_respects_limit(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """list_chats with limit returns at most limit items."""
        await adapter.create_chat(subject, title="A")
        await adapter.create_chat(subject, title="B")
        await adapter.create_chat(subject, title="C")
        result = await adapter.list_chats(subject, limit=2)
        assert len(result.items) == 2
        assert result.next_cursor is not None

    @pytest.mark.asyncio
    async def test_list_chats_with_cursor(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """list_chats with cursor returns next page."""
        c1 = await adapter.create_chat(subject, title="A")
        await adapter.create_chat(subject, title="B")
        await adapter.create_chat(subject, title="C")
        first = await adapter.list_chats(subject, limit=1)
        assert len(first.items) == 1
        assert first.next_cursor is not None
        second = await adapter.list_chats(subject, limit=1, cursor=first.next_cursor)
        assert len(second.items) == 1
        assert second.items[0].id != first.items[0].id

    @pytest.mark.asyncio
    async def test_list_chats_shared_with_me(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """list_chats_shared_with_me returns only chats shared with subject (not owned)."""
        from src.app_data.ports.types import ShareRole

        owner = subject
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        await adapter.create_chat(owner, title="Mine")
        shared = await adapter.create_chat(owner, title="Shared with grantee")
        await adapter.add_share(shared.id, owner, grantee, ShareRole.VIEWER)

        mine_page = await adapter.list_chats_shared_with_me(owner)
        assert mine_page.items == []

        grantee_page = await adapter.list_chats_shared_with_me(grantee)
        assert len(grantee_page.items) == 1
        assert grantee_page.items[0].id == shared.id
        assert grantee_page.items[0].title == "Shared with grantee"

    @pytest.mark.asyncio
    async def test_get_chat_with_share_access(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """get_chat returns chat when user has share access (viewer)."""
        from src.app_data.ports.types import ShareRole

        owner = subject
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        chat = await adapter.create_chat(owner, title="Shared")
        await adapter.add_share(chat.id, owner, grantee, ShareRole.VIEWER)
        found = await adapter.get_chat(chat.id, grantee)
        assert found is not None
        assert found.id == chat.id

    @pytest.mark.asyncio
    async def test_add_message_raises_for_viewer(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """add_message raises PermissionError when grantee is viewer (no edit)."""
        from src.app_data.ports.types import ShareRole

        owner = subject
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        chat = await adapter.create_chat(owner, title="Shared")
        await adapter.add_share(chat.id, owner, grantee, ShareRole.VIEWER)
        with pytest.raises(PermissionError, match="No edit access"):
            await adapter.add_message(chat.id, grantee, role="user", content="Hi")

    @pytest.mark.asyncio
    async def test_get_messages_with_cursor(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """get_messages with cursor returns paginated messages."""
        chat = await adapter.create_chat(subject, title="Chat")
        m1 = await adapter.add_message(chat.id, subject, role="user", content="M1")
        await adapter.add_message(chat.id, subject, role="user", content="M2")
        await adapter.add_message(chat.id, subject, role="user", content="M3")
        first = await adapter.get_messages(chat.id, subject, limit=1)
        assert len(first.items) == 1
        assert first.items[0].id == m1.id
        assert first.next_cursor is not None
        second = await adapter.get_messages(
            chat.id, subject, limit=1, cursor=first.next_cursor
        )
        assert len(second.items) == 1
        assert second.items[0].id != m1.id

    @pytest.mark.asyncio
    async def test_update_chat_folder_only(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """update_chat with folder_id only (update_folder=True)."""
        chat = await adapter.create_chat(subject, title="Chat")
        folder = await adapter.create_folder(subject, name="Dest")
        updated = await adapter.update_chat(
            chat.id, subject, folder_id=folder.id, update_folder=True
        )
        assert updated is not None
        assert updated.folder_id == folder.id
        assert updated.title == chat.title

    @pytest.mark.asyncio
    async def test_get_folder_requires_owner_not_shared_chat(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """Grantee with a shared chat in a folder cannot read the folder; chat access unchanged."""
        from src.app_data.ports.types import ShareRole

        owner = subject
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        folder = await adapter.create_folder(owner, name="Shared Folder")
        chat = await adapter.create_chat(owner, folder_id=folder.id, title="In Folder")
        await adapter.add_share(chat.id, owner, grantee, ShareRole.VIEWER)
        assert await adapter.get_folder(folder.id, grantee) is None
        assert await adapter.list_folders(grantee, parent_id=None) == []
        got_chat = await adapter.get_chat(chat.id, grantee)
        assert got_chat is not None
        assert got_chat.folder_id == folder.id

    @pytest.mark.asyncio
    async def test_list_chats_by_folder_requires_folder_ownership(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """Grantee cannot list chats by another user's folder_id even with shared chat inside."""
        from src.app_data.ports.types import ShareRole

        owner = subject
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        folder = await adapter.create_folder(owner, name="F")
        chat = await adapter.create_chat(owner, folder_id=folder.id, title="Shared")
        await adapter.add_share(chat.id, owner, grantee, ShareRole.VIEWER)
        scoped = await adapter.list_chats(grantee, folder_id=folder.id)
        assert scoped.items == []
        all_visible = await adapter.list_chats(grantee, folder_id=None)
        assert any(c.id == chat.id for c in all_visible.items)

    @pytest.mark.asyncio
    async def test_remove_share_when_none(self, adapter: MockChatAdapter, subject: Subject):
        """remove_share returns False when no share exists."""
        chat = await adapter.create_chat(subject, title="Chat")
        grantee = Subject(
            subject_type=SubjectType.USER,
            subject_id="660e8400-e29b-41d4-a716-446655440001",
        )
        ok = await adapter.remove_share(chat.id, subject, grantee)
        assert ok is False

    @pytest.mark.asyncio
    async def test_rename_folder(self, adapter: MockChatAdapter, subject: Subject):
        """rename_folder updates folder name."""
        folder = await adapter.create_folder(subject, name="Original")
        updated = await adapter.rename_folder(folder.id, subject, "Renamed")
        assert updated is not None
        assert updated.name == "Renamed"

    @pytest.mark.asyncio
    async def test_move_folder_rejects_self(self, adapter: MockChatAdapter, subject: Subject):
        """move_folder_to_parent returns None when moving into self."""
        folder = await adapter.create_folder(subject, name="Folder")
        result = await adapter.move_folder_to_parent(folder.id, subject, folder.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_move_folder_rejects_cycle(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """move_folder_to_parent returns None when move would create cycle."""
        parent = await adapter.create_folder(subject, name="Parent")
        child = await adapter.create_folder(
            subject, name="Child", parent_id=parent.id
        )
        # Moving parent into child would create cycle
        result = await adapter.move_folder_to_parent(parent.id, subject, child.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_folder(self, adapter: MockChatAdapter, subject: Subject):
        """delete_folder removes folder and moves chats to root."""
        folder = await adapter.create_folder(subject, name="To Delete")
        chat = await adapter.create_chat(subject, folder_id=folder.id, title="In Folder")
        ok = await adapter.delete_folder(folder.id, subject)
        assert ok is True
        found_folder = await adapter.get_folder(folder.id, subject)
        assert found_folder is None
        found_chat = await adapter.get_chat(chat.id, subject)
        assert found_chat is not None
        assert found_chat.folder_id is None

    @pytest.mark.asyncio
    async def test_delete_folder_moves_children_to_parent(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """delete_folder moves child folders to deleted folder's parent."""
        parent = await adapter.create_folder(subject, name="Parent")
        child = await adapter.create_folder(
            subject, name="Child", parent_id=parent.id
        )
        ok = await adapter.delete_folder(parent.id, subject)
        assert ok is True
        found = await adapter.get_folder(child.id, subject)
        assert found is not None
        assert found.parent_id is None

    @pytest.mark.asyncio
    async def test_list_folders_with_parent_id(
        self, adapter: MockChatAdapter, subject: Subject
    ):
        """list_folders with parent_id returns only children of that parent."""
        parent = await adapter.create_folder(subject, name="Parent")
        await adapter.create_folder(subject, name="Child1", parent_id=parent.id)
        await adapter.create_folder(subject, name="Child2", parent_id=parent.id)
        root_folders = await adapter.list_folders(subject, parent_id=None)
        assert len(root_folders) == 1
        assert root_folders[0].name == "Parent"
        child_folders = await adapter.list_folders(subject, parent_id=parent.id)
        assert len(child_folders) == 2
