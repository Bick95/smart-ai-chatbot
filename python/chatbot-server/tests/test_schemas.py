"""Tests for chat API schemas."""

import pytest
from pydantic import ValidationError

from src.server.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from src.settings import settings


@pytest.mark.unit
class TestChatMessage:
    def test_valid_roles(self):
        for role in ("user", "assistant", "system"):
            msg = ChatMessage(role=role, content="hello")
            assert msg.role == role
            assert msg.content == "hello"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid", content="hello")

    def test_content_max_length_enforced(self):
        max_len = settings.MAX_MESSAGE_CONTENT_LENGTH
        ChatMessage(role="user", content="x" * max_len)  # ok
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="x" * (max_len + 1))



@pytest.mark.unit
class TestChatRequest:
    def test_valid_single_message(self):
        req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
        assert len(req.messages) == 1
        assert req.messages[0].role == "user"
        assert req.messages[0].content == "hi"

    def test_valid_multiple_messages(self):
        req = ChatRequest(
            messages=[
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi there"},
                {"role": "user", "content": "how are you"},
            ]
        )
        assert len(req.messages) == 3

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

    def test_too_many_messages_rejected(self):
        max_msgs = settings.MAX_CHAT_MESSAGES
        messages = [{"role": "user", "content": "x"}] * max_msgs
        ChatRequest(messages=messages)  # ok at limit
        with pytest.raises(ValidationError):
            ChatRequest(messages=messages + [{"role": "user", "content": "y"}])


@pytest.mark.unit
class TestChatResponse:
    def test_valid_response(self):
        resp = ChatResponse(content="Hello, world!")
        assert resp.content == "Hello, world!"

    def test_empty_content_allowed(self):
        # Response might be empty in edge cases
        resp = ChatResponse(content="")
        assert resp.content == ""
