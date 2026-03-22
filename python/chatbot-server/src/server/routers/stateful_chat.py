"""Stateful chat API router: persisted chats, folders, sharing."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.state import CompiledStateGraph

from src.app_data.ports.chat_port import ChatPort
from src.app_data.ports.types import (
    Chat,
    ChatMessage,
    Folder,
    MessageRole,
    Subject,
    SubjectType,
)
from src.auth.ports.auth_port import AuthPort
from src.auth.utils.jwt import SubjectPayload
from src.chatbot.prompts import get_prompt_handler
from src.chatbot.state import AgentState
from src.server.dependencies import (
    get_agent_graph,
    get_auth,
    get_chat_port,
    get_current_subject,
)
from src.server.schemas.chat import (
    AddMessageRequest,
    AddMessageResponse,
    ChatCreateRequest,
    ChatListResponse,
    ChatMessageListResponse,
    ChatMessageResponseItem,
    ChatResponseItem,
    ChatUpdateRequest,
    FolderCreateRequest,
    FolderMoveRequest,
    FolderPatchRequest,
    FolderResponseItem,
    MoveChatToFolderRequest,
    ShareRequest,
    ShareResponseItem,
    UserSearchResponseItem,
)
from src.utils.logging import get_logger
from src.utils.messages import to_langchain_messages

logger = get_logger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


def _subject_from_payload(payload: SubjectPayload) -> Subject:
    """Convert SubjectPayload to Subject for app_data layer."""
    return Subject(
        subject_type=SubjectType(payload.subject_type.value),
        subject_id=payload.subject_id,
    )


def _chat_to_response(chat: Chat) -> ChatResponseItem:
    return ChatResponseItem(
        id=chat.id,
        owner_subject=chat.owner_subject,
        folder_id=chat.folder_id,
        title=chat.title,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
    )


def _message_to_response(msg) -> ChatMessageResponseItem:
    return ChatMessageResponseItem(
        id=msg.id,
        chat_id=msg.chat_id,
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at.isoformat(),
    )


def _folder_to_response(folder: Folder) -> FolderResponseItem:
    return FolderResponseItem(
        id=folder.id,
        owner_subject=folder.owner_subject,
        parent_id=folder.parent_id,
        name=folder.name,
        system_prompt=folder.system_prompt,
        created_at=folder.created_at.isoformat(),
        updated_at=folder.updated_at.isoformat(),
    )


# --- Chats ---


@router.post("", response_model=ChatResponseItem)
async def create_chat(
    body: ChatCreateRequest | None = Body(default=None),
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatResponseItem:
    """Create a new chat. System prompt is fetched from folder on each request, not stored."""
    subj = _subject_from_payload(subject)
    folder_id = body.folder_id if body else None
    title = body.title if body else None
    c = await chat_port.create_chat(subj, folder_id=folder_id, title=title)
    return _chat_to_response(c)


@router.get("", response_model=ChatListResponse)
async def list_chats(
    folder_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatListResponse:
    """List chats (paginated, optionally filtered by folder)."""
    subj = _subject_from_payload(subject)
    result = await chat_port.list_chats(
        subj, folder_id=folder_id, limit=limit, cursor=cursor
    )
    return ChatListResponse(
        items=[_chat_to_response(c) for c in result.items],
        next_cursor=result.next_cursor,
    )


@router.get("/{chat_id}", response_model=ChatResponseItem)
async def get_chat(
    chat_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatResponseItem:
    """Get chat metadata."""
    subj = _subject_from_payload(subject)
    c = await chat_port.get_chat(chat_id, subj)
    if c is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_to_response(c)


@router.patch("/{chat_id}", response_model=ChatResponseItem)
async def update_chat(
    chat_id: str,
    body: ChatUpdateRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatResponseItem:
    """Update chat (rename and/or move to folder)."""
    subj = _subject_from_payload(subject)
    update_title = "title" in body.model_fields_set
    update_folder = "folder_id" in body.model_fields_set
    if not update_title and not update_folder:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of title or folder_id to update",
        )
    c = await chat_port.update_chat(
        chat_id,
        subj,
        title=body.title,
        folder_id=body.folder_id,
        update_title=update_title,
        update_folder=update_folder,
    )
    if c is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_to_response(c)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> None:
    """Delete chat (owner only)."""
    subj = _subject_from_payload(subject)
    ok = await chat_port.delete_chat(chat_id, subj)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")


# --- Messages ---


@router.get("/{chat_id}/messages", response_model=ChatMessageListResponse)
async def get_messages(
    chat_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatMessageListResponse:
    """Get messages (paginated)."""
    subj = _subject_from_payload(subject)
    c = await chat_port.get_chat(chat_id, subj)
    if c is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    result = await chat_port.get_messages(chat_id, subj, limit=limit, cursor=cursor)
    return ChatMessageListResponse(
        items=[_message_to_response(m) for m in result.items],
        next_cursor=result.next_cursor,
    )


@router.post("/{chat_id}/messages", response_model=AddMessageResponse)
async def add_message(
    chat_id: str,
    body: AddMessageRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    agent: CompiledStateGraph[AgentState, None, AgentState, AgentState] = Depends(
        get_agent_graph
    ),
    subject: SubjectPayload = Depends(get_current_subject),
) -> AddMessageResponse:
    """Add a message. If role is user and generate_reply is true, get AI reply.
    Users can only add 'user' messages; assistant/system would corrupt history."""
    if body.role != MessageRole.USER:
        raise HTTPException(
            status_code=400,
            detail="Only 'user' messages can be added via this endpoint",
        )
    subj = _subject_from_payload(subject)
    try:
        msg = await chat_port.add_message(
            chat_id, subj, body.role, body.content
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="No edit access to this chat")
    except ValueError:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Auto-name chat from first user message if no title
    if body.role == MessageRole.USER and body.content.strip():
        chat = await chat_port.get_chat(chat_id, subj)
        if chat and (not chat.title or not chat.title.strip()):
            title = body.content.strip()[:30]
            if title:
                await chat_port.update_chat(
                    chat_id, subj, title=title, update_title=True
                )

    reply_content: str | None = None

    if body.role == MessageRole.USER and body.generate_reply:
        try:
            # Get chat to resolve folder (for dynamic system prompt)
            chat = await chat_port.get_chat(chat_id, subj)
            system_prompt: str | None = None
            if chat and chat.folder_id:
                folder = await chat_port.get_folder(chat.folder_id, subj)
                if folder and folder.system_prompt:
                    system_prompt = folder.system_prompt

            # Get conversation history (includes the message we just added)
            history = await chat_port.get_messages(
                chat_id, subj, limit=50, cursor=None
            )
            messages = history.items

            # Build langchain messages; prepend system prompt from folder (not stored in history)
            raw_messages = [{"role": m.role.value, "content": m.content} for m in messages]
            if system_prompt:
                raw_messages.insert(0, {"role": "system", "content": system_prompt})
            langchain_messages = to_langchain_messages(raw_messages)
            result: dict = await agent.ainvoke({"messages": langchain_messages})
            result_messages: List[AnyMessage] = result.get("messages", [])
            if result_messages:
                last = result_messages[-1]
                if isinstance(last, AIMessage) and last.content:
                    reply_content = (
                        last.content
                        if isinstance(last.content, str)
                        else str(last.content)
                    )
                    await chat_port.add_message(
                        chat_id, subj, MessageRole.ASSISTANT, reply_content
                    )
        except Exception:
            logger.exception("Error generating reply in stateful_chat")
            reply_content = get_prompt_handler().get(
                "server.stateless_chat.fallback"
            )

    return AddMessageResponse(
        message=_message_to_response(msg),
        reply=reply_content,
    )


# --- Shares ---


@router.get("/{chat_id}/shares")
async def list_shares(
    chat_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> list[ShareResponseItem]:
    """List shares for a chat (owner only)."""
    subj = _subject_from_payload(subject)
    c = await chat_port.get_chat(chat_id, subj)
    if c is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if c.owner_subject != subj.to_str():
        raise HTTPException(status_code=403, detail="Only the owner can list shares")
    shares = await chat_port.list_shares(chat_id, subj)
    return [
        ShareResponseItem(
            chat_id=s.chat_id,
            subject=s.subject,
            role=s.role,
            created_at=s.created_at.isoformat(),
        )
        for s in shares
    ]


@router.post("/{chat_id}/shares", response_model=ShareResponseItem)
async def add_share(
    chat_id: str,
    body: ShareRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ShareResponseItem:
    """Add share (owner only)."""
    owner = _subject_from_payload(subject)
    grantee = Subject(subject_type=body.subject_type, subject_id=body.subject_id)
    if grantee.to_str() == owner.to_str():
        raise HTTPException(
            status_code=400,
            detail="Cannot share a chat with yourself",
        )
    try:
        share = await chat_port.add_share(chat_id, owner, grantee, body.role)
        return ShareResponseItem(
            chat_id=share.chat_id,
            subject=share.subject,
            role=share.role,
            created_at=share.created_at.isoformat(),
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not the chat owner")


@router.delete("/{chat_id}/shares/{subject_type}/{subject_id}", status_code=204)
async def remove_share(
    chat_id: str,
    subject_type: str,
    subject_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> None:
    """Remove share (owner only)."""
    owner = _subject_from_payload(subject)
    grantee = Subject(subject_type=SubjectType(subject_type), subject_id=subject_id)
    ok = await chat_port.remove_share(chat_id, owner, grantee)
    if not ok:
        raise HTTPException(status_code=404, detail="Share not found")


# --- Folders (separate router prefix) ---

folders_router = APIRouter(prefix="/folders", tags=["folders"])


@folders_router.get("", response_model=list[FolderResponseItem])
async def list_folders(
    parent_id: str | None = Query(default=None),
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> list[FolderResponseItem]:
    """List folders (root if parent_id omitted)."""
    subj = _subject_from_payload(subject)
    folders = await chat_port.list_folders(subj, parent_id=parent_id)
    return [_folder_to_response(f) for f in folders]


@folders_router.get("/{folder_id}", response_model=FolderResponseItem)
async def get_folder(
    folder_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> FolderResponseItem:
    """Get a single folder by ID."""
    subj = _subject_from_payload(subject)
    folder = await chat_port.get_folder(folder_id, subj)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return _folder_to_response(folder)


@folders_router.post("", response_model=FolderResponseItem)
async def create_folder(
    body: FolderCreateRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> FolderResponseItem:
    """Create a folder."""
    subj = _subject_from_payload(subject)
    folder = await chat_port.create_folder(
        subj, body.name, parent_id=body.parent_id, system_prompt=body.system_prompt
    )
    return _folder_to_response(folder)


@folders_router.patch("/{folder_id}", response_model=FolderResponseItem)
async def patch_folder(
    folder_id: str,
    body: FolderPatchRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> FolderResponseItem:
    """Update a folder (name and/or system_prompt)."""
    subj = _subject_from_payload(subject)
    patch_kwargs: dict[str, str | None] = {}
    if "name" in body.model_fields_set and body.name:
        patch_kwargs["name"] = body.name
    if "system_prompt" in body.model_fields_set:
        patch_kwargs["system_prompt"] = body.system_prompt
    folder = await chat_port.update_folder(folder_id, subj, **patch_kwargs)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return _folder_to_response(folder)


@folders_router.patch("/{folder_id}/parent", response_model=FolderResponseItem)
async def move_folder(
    folder_id: str,
    body: FolderMoveRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> FolderResponseItem:
    """Move folder to another parent. parent_id=null moves to root."""
    subj = _subject_from_payload(subject)
    folder = await chat_port.move_folder_to_parent(
        folder_id, subj, body.parent_id
    )
    if folder is None:
        raise HTTPException(
            status_code=400,
            detail="Folder not found or move would create a cycle",
        )
    return _folder_to_response(folder)


@folders_router.delete("/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: str,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> None:
    """Delete a folder (chats move to parent or root)."""
    subj = _subject_from_payload(subject)
    ok = await chat_port.delete_folder(folder_id, subj)
    if not ok:
        raise HTTPException(status_code=404, detail="Folder not found")


# --- Move chat to folder ---

@router.patch("/{chat_id}/folder", response_model=ChatResponseItem)
async def move_chat_to_folder(
    chat_id: str,
    body: MoveChatToFolderRequest,
    chat_port: ChatPort = Depends(get_chat_port),
    subject: SubjectPayload = Depends(get_current_subject),
) -> ChatResponseItem:
    """Move chat to folder (body.folder_id=None moves to root)."""
    subj = _subject_from_payload(subject)
    ok = await chat_port.move_chat_to_folder(chat_id, subj, body.folder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    c = await chat_port.get_chat(chat_id, subj)
    if c is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_to_response(c)


# --- User search (for sharing) ---

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/search", response_model=list[UserSearchResponseItem])
async def search_users(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=50),
    auth: AuthPort = Depends(get_auth),
    subject: SubjectPayload = Depends(get_current_subject),
) -> list[UserSearchResponseItem]:
    """Search users by username (for adding as editors/viewers)."""
    users = await auth.search_users_by_username(q, limit=limit)
    return [
        UserSearchResponseItem(id=u.id, username=u.username)
        for u in users
    ]
