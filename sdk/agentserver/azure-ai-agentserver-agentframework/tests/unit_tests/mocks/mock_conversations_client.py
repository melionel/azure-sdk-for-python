# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Mock implementation of OpenAI Conversations client for testing."""

from typing import Any, Iterator, Optional
from dataclasses import dataclass, field


@dataclass
class MockItemContentInputText:
    """Mock ItemContentInputText."""
    text: str
    type: str = "input_text"


@dataclass
class MockItemContentOutputText:
    """Mock ItemContentOutputText."""
    text: str
    type: str = "output_text"
    annotations: list = field(default_factory=list)


@dataclass
class MockResponsesMessageItemResource:
    """Mock ResponsesMessageItemResource."""
    id: str
    role: str
    content: list
    type: str = "message"
    status: str = "completed"


class MockConversationItems:
    """Mock conversations.items client."""

    def __init__(self, items: Optional[list[MockResponsesMessageItemResource]] = None) -> None:
        self._items = items or []

    def list(self, conversation_id: str) -> Iterator[MockResponsesMessageItemResource]:
        """List items in a conversation."""
        return iter(self._items)

    def set_items(self, items: list[MockResponsesMessageItemResource]) -> None:
        """Set the items to be returned by list()."""
        self._items = items


class MockConversations:
    """Mock conversations client."""

    def __init__(self) -> None:
        self.items = MockConversationItems()


class MockOpenAIClient:
    """Mock OpenAI client with conversations API."""

    def __init__(self) -> None:
        self.conversations = MockConversations()

    def __enter__(self) -> "MockOpenAIClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class MockAIProjectClient:
    """Mock AIProjectClient for testing."""

    def __init__(self, endpoint: str = "", credential: Any = None) -> None:
        self._endpoint = endpoint
        self._credential = credential
        self._openai_client = MockOpenAIClient()

    def get_openai_client(self) -> MockOpenAIClient:
        """Get the mock OpenAI client."""
        return self._openai_client

    def __enter__(self) -> "MockAIProjectClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass
