"""Tests for prompt handler."""

import pytest

from src.chatbot.prompts import get_prompt_handler


@pytest.mark.unit
class TestPromptHandler:
    def test_resolves_node_prompts(self):
        handler = get_prompt_handler()
        system = handler.get("nodes.llm_node.system")
        assert isinstance(system, str)
        assert "assistant" in system.lower()
        fallback = handler.get("nodes.llm_node.fallback")
        assert "Sorry" in fallback

    def test_resolves_tool_prompts(self):
        handler = get_prompt_handler()
        system = handler.get("tools.summarize_text.system")
        assert isinstance(system, str)
        assert "summar" in system.lower()

    def test_resolves_server_prompts(self):
        handler = get_prompt_handler()
        fallback = handler.get("server.stateless_chat.fallback")
        assert "Sorry" in fallback

    def test_unknown_prompt_raises(self):
        handler = get_prompt_handler()
        with pytest.raises(ValueError, match="Prompt not found"):
            handler.get("nonexistent.prompt.id")

    def test_get_optional_returns_default(self):
        handler = get_prompt_handler()
        result = handler.get_optional("nonexistent.prompt.id", default="fallback")
        assert result == "fallback"
