# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from collections.abc import MutableMapping, Sequence
from typing import Any, Optional, Union

from agent_framework import ChatMessage

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ItemContentInputText,
    ItemContentOutputText,
    ItemType,
    ResponsesMessageItemResource,
)


def _convert_item_to_chat_message(item: ResponsesMessageItemResource) -> Optional[ChatMessage]:
    """Convert an ItemResource from the Conversations API to a ChatMessage.

    :param item: The item resource from the Conversations API.
    :type item: ResponsesMessageItemResource
    :return: The converted ChatMessage, or None if conversion is not possible.
    :rtype: Optional[ChatMessage]
    """
    if item.type != ItemType.MESSAGE:
        return None

    role = str(item.role).lower()
    content_parts = []

    if hasattr(item, "content") and item.content:
        for content_item in item.content:
            if isinstance(content_item, ItemContentInputText):
                content_parts.append(content_item.text)
            elif isinstance(content_item, ItemContentOutputText):
                content_parts.append(content_item.text)

    if not content_parts:
        return None

    return ChatMessage(role=role, content="\n".join(content_parts))


class FoundryConversationMessageStore:
    """A ChatMessageStoreProtocol implementation that reads messages from Azure AI Foundry Conversations API.

    This message store fetches messages from the Foundry Conversations API and converts them
    to ChatMessage format. Messages added via add_messages() are cached locally but not
    persisted back to the API.

    :param conversation_id: The conversation ID to fetch messages from.
    :type conversation_id: str
    :param project_endpoint: The Azure AI Foundry project endpoint.
    :type project_endpoint: str
    :param credentials: The token credential for authentication.
    :type credentials: Union[TokenCredential, AsyncTokenCredential]
    """

    def __init__(
        self,
        conversation_id: str,
        project_endpoint: str,
        credentials: Union[TokenCredential, AsyncTokenCredential],
        *,
        _project_client_factory: Optional[Any] = None,
    ) -> None:
        """Initialize the FoundryConversationMessageStore.

        :param conversation_id: The conversation ID to fetch messages from.
        :type conversation_id: str
        :param project_endpoint: The Azure AI Foundry project endpoint.
        :type project_endpoint: str
        :param credentials: The token credential for authentication.
        :type credentials: Union[TokenCredential, AsyncTokenCredential]
        :keyword _project_client_factory: Optional factory for creating project client (for testing).
        :paramtype _project_client_factory: Optional[Any]
        """
        self._conversation_id = conversation_id
        self._project_endpoint = project_endpoint
        self._credentials = credentials
        self._cached_messages: list[ChatMessage] = []
        self._project_client_factory = _project_client_factory

    @property
    def conversation_id(self) -> str:
        """Get the conversation ID.

        :return: The conversation ID.
        :rtype: str
        """
        return self._conversation_id

    def _create_project_client(self) -> Any:
        """Create a project client instance.

        :return: The project client.
        :rtype: Any
        """
        if self._project_client_factory is not None:
            return self._project_client_factory()
        return AIProjectClient(
            endpoint=self._project_endpoint,
            credential=self._credentials,  # type: ignore
        )

    async def list_messages(self) -> list[ChatMessage]:
        """Get all messages from the conversation, including cached messages.

        Fetches messages from the Foundry Conversations API, converts them to ChatMessage format,
        and combines them with any locally cached messages.

        :return: List of ChatMessage objects, ordered from oldest to newest.
        :rtype: list[ChatMessage]
        """
        api_messages: list[ChatMessage] = []

        with self._create_project_client() as project_client:
            with project_client.get_openai_client() as openai_client:
                for item in openai_client.conversations.items.list(self._conversation_id):
                    if isinstance(item, ResponsesMessageItemResource):
                        chat_message = _convert_item_to_chat_message(item)
                        if chat_message:
                            api_messages.append(chat_message)

        # Combine API messages with cached messages
        return api_messages + self._cached_messages

    async def add_messages(self, messages: Sequence[ChatMessage]) -> None:
        """Add messages to the local cache.

        Messages are cached locally but not persisted to the API.

        :param messages: The sequence of ChatMessage objects to add.
        :type messages: Sequence[ChatMessage]
        """
        self._cached_messages.extend(messages)

    @classmethod
    async def deserialize(
        cls,
        serialized_store_state: MutableMapping[str, Any],
        *,
        project_endpoint: Optional[str] = None,
        credentials: Optional[Union[TokenCredential, AsyncTokenCredential]] = None,
        **kwargs: Any,
    ) -> "FoundryConversationMessageStore":
        """Create a new FoundryConversationMessageStore instance from serialized state.

        :param serialized_store_state: The serialized state data.
        :type serialized_store_state: MutableMapping[str, Any]
        :keyword project_endpoint: The Azure AI Foundry project endpoint.
        :paramtype project_endpoint: Optional[str]
        :keyword credentials: The token credential for authentication.
        :paramtype credentials: Optional[Union[TokenCredential, AsyncTokenCredential]]
        :return: A new FoundryConversationMessageStore instance.
        :rtype: FoundryConversationMessageStore
        :raises ValueError: If required parameters are missing.
        """
        conversation_id = serialized_store_state.get("conversation_id")
        if not conversation_id:
            raise ValueError("conversation_id is required in serialized state")
        if not project_endpoint:
            raise ValueError("project_endpoint is required for deserialization")
        if not credentials:
            raise ValueError("credentials is required for deserialization")

        store = cls(
            conversation_id=conversation_id,
            project_endpoint=project_endpoint,
            credentials=credentials,
        )

        # Restore cached messages
        cached_messages_data = serialized_store_state.get("messages", [])
        for msg_data in cached_messages_data:
            if isinstance(msg_data, dict):
                store._cached_messages.append(ChatMessage.from_dict(msg_data))
            elif isinstance(msg_data, ChatMessage):
                store._cached_messages.append(msg_data)

        return store

    async def update_from_state(
        self,
        serialized_store_state: MutableMapping[str, Any],
        **kwargs: Any,
    ) -> None:
        """Update the current store instance from serialized state data.

        :param serialized_store_state: The serialized state data.
        :type serialized_store_state: MutableMapping[str, Any]
        """
        if not serialized_store_state:
            return

        # Update cached messages
        cached_messages_data = serialized_store_state.get("messages", [])
        self._cached_messages = []
        for msg_data in cached_messages_data:
            if isinstance(msg_data, dict):
                self._cached_messages.append(ChatMessage.from_dict(msg_data))
            elif isinstance(msg_data, ChatMessage):
                self._cached_messages.append(msg_data)

    async def serialize(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize the current store state.

        :return: The serialized state data containing conversation_id and cached messages.
        :rtype: dict[str, Any]
        """
        return {
            "conversation_id": self._conversation_id,
            "messages": [msg.to_dict() for msg in self._cached_messages],
        }
