# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Unit tests for FoundryConversationAgentThread."""

import pytest
from agent_framework import ChatMessage

from azure.ai.agentserver.agentframework.persistence import (
    FoundryConversationAgentThread,
    FoundryConversationMessageStore,
)

from .mocks import (
    MockAIProjectClient,
    MockResponsesMessageItemResource,
    MockItemContentInputText,
)


class MockCredential:
    """Mock credential for testing."""
    pass


def create_mock_client_factory(items: list[MockResponsesMessageItemResource]):
    """Create a factory that returns a MockAIProjectClient with the given items."""
    def factory():
        client = MockAIProjectClient()
        client.get_openai_client().conversations.items.set_items(items)
        return client
    return factory


@pytest.mark.unit
@pytest.mark.asyncio
async def test_thread_has_conversation_id() -> None:
    """Test that thread has conversation_id property."""
    thread = FoundryConversationAgentThread(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    assert thread.conversation_id == "conv-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_thread_has_message_store() -> None:
    """Test that thread has a message store."""
    thread = FoundryConversationAgentThread(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    assert thread.message_store is not None
    assert isinstance(thread.message_store, FoundryConversationMessageStore)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_thread_is_initialized() -> None:
    """Test that thread is initialized."""
    thread = FoundryConversationAgentThread(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    assert thread.is_initialized is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_serialize_includes_conversation_id() -> None:
    """Test that serialize includes conversation_id."""
    thread = FoundryConversationAgentThread(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    serialized = await thread.serialize()

    assert serialized["conversation_id"] == "conv-123"
    assert "chat_message_store_state" in serialized


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_creates_thread_with_conversation_id() -> None:
    """Test that deserialize creates thread with conversation_id."""
    serialized_state = {
        "conversation_id": "conv-456",
        "chat_message_store_state": {
            "conversation_id": "conv-456",
            "messages": [],
        },
    }

    thread = await FoundryConversationAgentThread.deserialize(
        serialized_state,
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    assert thread.conversation_id == "conv-456"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_conversation_id() -> None:
    """Test that deserialize raises ValueError without conversation_id."""
    with pytest.raises(ValueError, match="conversation_id is required"):
        await FoundryConversationAgentThread.deserialize(
            {},
            project_endpoint="https://test.endpoint",
            credentials=MockCredential(),
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_project_endpoint() -> None:
    """Test that deserialize raises ValueError without project_endpoint."""
    with pytest.raises(ValueError, match="project_endpoint is required"):
        await FoundryConversationAgentThread.deserialize(
            {"conversation_id": "conv-123"},
            credentials=MockCredential(),
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_credentials() -> None:
    """Test that deserialize raises ValueError without credentials."""
    with pytest.raises(ValueError, match="credentials is required"):
        await FoundryConversationAgentThread.deserialize(
            {"conversation_id": "conv-123"},
            project_endpoint="https://test.endpoint",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_restores_message_store_state() -> None:
    """Test that deserialize restores message store state."""
    serialized_state = {
        "conversation_id": "conv-456",
        "chat_message_store_state": {
            "conversation_id": "conv-456",
            "messages": [{"role": "user", "content": "Restored message"}],
        },
    }

    thread = await FoundryConversationAgentThread.deserialize(
        serialized_state,
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    # Check that cached messages were restored
    store = thread.message_store
    assert isinstance(store, FoundryConversationMessageStore)
    assert len(store._cached_messages) == 1
    assert store._cached_messages[0].content == "Restored message"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_from_thread_state() -> None:
    """Test that update_from_thread_state updates the message store."""
    thread = FoundryConversationAgentThread(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    await thread.update_from_thread_state({
        "chat_message_store_state": {
            "messages": [{"role": "user", "content": "Updated message"}],
        },
    })

    store = thread.message_store
    assert isinstance(store, FoundryConversationMessageStore)
    assert len(store._cached_messages) == 1
    assert store._cached_messages[0].content == "Updated message"
