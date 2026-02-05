# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Unit tests for FoundryConversationThreadRepository."""

import pytest

from azure.ai.agentserver.agentframework.persistence import (
    FoundryConversationThreadRepository,
    FoundryConversationAgentThread,
)


class MockCredential:
    """Mock credential for testing."""
    pass


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_returns_none_for_none_conversation_id() -> None:
    """Test that get returns None for None conversation_id."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread = await repo.get(None)

    assert thread is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_creates_new_thread() -> None:
    """Test that get creates a new thread for a conversation_id."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread = await repo.get("conv-123")

    assert thread is not None
    assert isinstance(thread, FoundryConversationAgentThread)
    assert thread.conversation_id == "conv-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_returns_cached_thread() -> None:
    """Test that get returns the same cached thread for the same conversation_id."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread1 = await repo.get("conv-123")
    thread2 = await repo.get("conv-123")

    assert thread1 is thread2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_creates_different_threads_for_different_ids() -> None:
    """Test that get creates different threads for different conversation_ids."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread1 = await repo.get("conv-123")
    thread2 = await repo.get("conv-456")

    assert thread1 is not thread2
    assert thread1.conversation_id == "conv-123"
    assert thread2.conversation_id == "conv-456"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_stores_thread() -> None:
    """Test that set stores a thread in the cache."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread = FoundryConversationAgentThread(
        conversation_id="conv-789",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    await repo.set("conv-789", thread)

    retrieved = await repo.get("conv-789")
    assert retrieved is thread


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_ignores_none_conversation_id() -> None:
    """Test that set ignores None conversation_id."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    thread = FoundryConversationAgentThread(
        conversation_id="conv-789",
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    await repo.set(None, thread)

    # Should not raise and internal cache should be empty
    assert len(repo._threads) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_set_ignores_none_thread() -> None:
    """Test that set ignores None thread."""
    repo = FoundryConversationThreadRepository(
        project_endpoint="https://test.endpoint",
        credentials=MockCredential(),
    )

    await repo.set("conv-123", None)

    # Should not raise and internal cache should be empty
    assert len(repo._threads) == 0
