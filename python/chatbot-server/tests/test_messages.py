"""Tests for message conversion utilities."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.utils.messages import to_langchain_messages


@pytest.mark.unit
class TestToLangchainMessages:
    def test_user_message(self):
        result = to_langchain_messages([{"role": "user", "content": "hello"}])
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "hello"

    def test_assistant_message(self):
        result = to_langchain_messages([{"role": "assistant", "content": "hi back"}])
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "hi back"

    def test_system_message(self):
        result = to_langchain_messages(
            [{"role": "system", "content": "You are helpful"}]
        )
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "You are helpful"

    def test_mixed_conversation(self):
        result = to_langchain_messages(
            [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
                {"role": "user", "content": "thanks"},
            ]
        )
        assert len(result) == 3
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert isinstance(result[2], HumanMessage)

    def test_default_role_user(self):
        result = to_langchain_messages([{"content": "hello"}])
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)

    def test_default_content_empty(self):
        result = to_langchain_messages([{"role": "user"}])
        assert len(result) == 1
        assert result[0].content == ""

    def test_invalid_role_skipped(self):
        result = to_langchain_messages(
            [
                {"role": "user", "content": "valid"},
                {"role": "unknown", "content": "skipped"},
                {"role": "assistant", "content": "valid2"},
            ]
        )
        assert len(result) == 2
        assert result[0].content == "valid"
        assert result[1].content == "valid2"

    def test_empty_input(self):
        result = to_langchain_messages([])
        assert result == []
