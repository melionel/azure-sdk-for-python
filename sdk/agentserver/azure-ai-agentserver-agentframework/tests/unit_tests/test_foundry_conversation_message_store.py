# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Unit tests for FoundryConversationMessageStore."""

import pytest
from agent_framework import ChatMessage

from azure.ai.agentserver.agentframework.persistence import FoundryConversationMessageStore

from .mocks import (
    MockAIProjectClient,
    MockResponsesMessageItemResource,
    MockItemContentInputText,
    MockItemContentOutputText,
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
async def test_list_messages_returns_api_messages() -> None:
    """Test that list_messages returns messages from the API."""
    items = [
        MockResponsesMessageItemResource(
            id="item-1",
            role="user",
            content=[MockItemContentInputText(text="Hello")],
        ),
        MockResponsesMessageItemResource(
            id="item-2",
            role="assistant",
            content=[MockItemContentOutputText(text="Hi there!")],
        ),
    ]

    store = FoundryConversationMessageStore(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory(items),
    )

    messages = await store.list_messages()

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Hi there!"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_messages_combines_api_and_cached_messages() -> None:
    """Test that list_messages combines API messages with cached messages."""
    items = [
        MockResponsesMessageItemResource(
            id="item-1",
            role="user",
            content=[MockItemContentInputText(text="Hello")],
        ),
    ]

    store = FoundryConversationMessageStore(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory(items),
    )

    # Add a cached message
    await store.add_messages([ChatMessage(role="assistant", content="Cached response")])

    messages = await store.list_messages()

    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Cached response"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_messages_caches_locally() -> None:
    """Test that add_messages caches messages locally."""
    store = FoundryConversationMessageStore(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory([]),
    )

    await store.add_messages([
        ChatMessage(role="user", content="Message 1"),
        ChatMessage(role="assistant", content="Message 2"),
    ])

    # Access cached messages directly
    assert len(store._cached_messages) == 2
    assert store._cached_messages[0].content == "Message 1"
    assert store._cached_messages[1].content == "Message 2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_serialize_returns_conversation_id_and_messages() -> None:
    """Test that serialize returns conversation_id and cached messages."""
    store = FoundryConversationMessageStore(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory([]),
    )

    await store.add_messages([ChatMessage(role="user", content="Test message")])

    serialized = await store.serialize()

    assert serialized["conversation_id"] == "conv-123"
    assert len(serialized["messages"]) == 1
    assert serialized["messages"][0]["content"] == "Test message"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_restores_cached_messages() -> None:
    """Test that deserialize restores cached messages from state."""
    serialized_state = {
        "conversation_id": "conv-456",
        "messages": [
            {"role": "user", "content": "Restored message"},
        ],
    }

    store = await FoundryConversationMessageStore.deserialize(
        serialized_state,
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    assert store.conversation_id == "conv-456"
    assert len(store._cached_messages) == 1
    assert store._cached_messages[0].content == "Restored message"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_conversation_id() -> None:
    """Test that deserialize raises ValueError without conversation_id."""
    with pytest.raises(ValueError, match="conversation_id is required"):
        await FoundryConversationMessageStore.deserialize(
            {},
            project_endpoint="https://test.endpoint",
            credentials=MockCredential(),
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_project_endpoint() -> None:
    """Test that deserialize raises ValueError without project_endpoint."""
    with pytest.raises(ValueError, match="project_endpoint is required"):
        await FoundryConversationMessageStore.deserialize(
            {"conversation_id": "conv-123"},
            credentials=MockCredential(),
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deserialize_raises_without_credentials() -> None:
    """Test that deserialize raises ValueError without credentials."""
    with pytest.raises(ValueError, match="credentials is required"):
        await FoundryConversationMessageStore.deserialize(
            {"conversation_id": "conv-123"},
            project_endpoint="https://test.endpoint",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_from_state_updates_cached_messages() -> None:
    """Test that update_from_state updates cached messages."""
    store = FoundryConversationMessageStore(
        conversation_id="conv-123",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory([]),
    )

    await store.add_messages([ChatMessage(role="user", content="Original")])

    await store.update_from_state({
        "messages": [{"role": "assistant", "content": "Updated"}],
    })

    assert len(store._cached_messages) == 1
    assert store._cached_messages[0].content == "Updated"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_conversation_id_property() -> None:
    """Test that conversation_id property returns correct value."""
    store = FoundryConversationMessageStore(
        conversation_id="my-conversation",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
        _project_client_factory=create_mock_client_factory([]),
    )

    assert store.conversation_id == "my-conversation"
