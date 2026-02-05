# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from collections.abc import MutableMapping
from typing import Any, Optional, Union

from agent_framework import AgentThread, ChatMessage

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential

from ._foundry_conversation_message_store import FoundryConversationMessageStore


class FoundryConversationAgentThread(AgentThread):
    """An AgentThread implementation that uses Azure AI Foundry Conversations API for message storage.

    This thread maintains a conversation_id and uses FoundryConversationMessageStore to fetch
    messages from the Foundry Conversations API.

    :param conversation_id: The conversation ID.
    :type conversation_id: str
    :param project_endpoint: The Azure AI Foundry project endpoint.
    :type project_endpoint: str
    :param credentials: The token credential for authentication.
    :type credentials: Union[TokenCredential, AsyncTokenCredential]
    """

    def __init__(
        self,
        *,
        conversation_id: str,
        project_endpoint: str,
        credentials: Union[TokenCredential, AsyncTokenCredential],
    ) -> None:
        """Initialize the FoundryConversationAgentThread.

        :keyword conversation_id: The conversation ID.
        :paramtype conversation_id: str
        :keyword project_endpoint: The Azure AI Foundry project endpoint.
        :paramtype project_endpoint: str
        :keyword credentials: The token credential for authentication.
        :paramtype credentials: Union[TokenCredential, AsyncTokenCredential]
        """
        self._conversation_id = conversation_id
        self._project_endpoint = project_endpoint
        self._credentials = credentials

        message_store = FoundryConversationMessageStore(
            conversation_id=conversation_id,
            project_endpoint=project_endpoint,
            credentials=credentials,
        )

        super().__init__(message_store=message_store)

    @property
    def conversation_id(self) -> str:
        """Get the conversation ID.

        :return: The conversation ID.
        :rtype: str
        """
        return self._conversation_id

    async def serialize(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize the current thread state.

        :return: The serialized state data containing conversation_id and message store state.
        :rtype: dict[str, Any]
        """
        result: dict[str, Any] = {
            "conversation_id": self._conversation_id,
        }

        if self._message_store is not None:
            result["chat_message_store_state"] = await self._message_store.serialize(**kwargs)

        return result

    @classmethod
    async def deserialize(
        cls,
        serialized_thread_state: MutableMapping[str, Any],
        *,
        project_endpoint: Optional[str] = None,
        credentials: Optional[Union[TokenCredential, AsyncTokenCredential]] = None,
        message_store: Optional[FoundryConversationMessageStore] = None,
        **kwargs: Any,
    ) -> "FoundryConversationAgentThread":
        """Deserialize the state from a dictionary into a new FoundryConversationAgentThread instance.

        :param serialized_thread_state: The serialized thread state as a dictionary.
        :type serialized_thread_state: MutableMapping[str, Any]
        :keyword project_endpoint: The Azure AI Foundry project endpoint.
        :paramtype project_endpoint: Optional[str]
        :keyword credentials: The token credential for authentication.
        :paramtype credentials: Optional[Union[TokenCredential, AsyncTokenCredential]]
        :keyword message_store: Optional existing message store to use.
        :paramtype message_store: Optional[FoundryConversationMessageStore]
        :return: A new FoundryConversationAgentThread instance.
        :rtype: FoundryConversationAgentThread
        :raises ValueError: If required parameters are missing.
        """
        conversation_id = serialized_thread_state.get("conversation_id")
        if not conversation_id:
            raise ValueError("conversation_id is required in serialized state")
        if not project_endpoint:
            raise ValueError("project_endpoint is required for deserialization")
        if not credentials:
            raise ValueError("credentials is required for deserialization")

        thread = cls(
            conversation_id=conversation_id,
            project_endpoint=project_endpoint,
            credentials=credentials,
        )

        # Restore message store state if present
        chat_message_store_state = serialized_thread_state.get("chat_message_store_state")
        if chat_message_store_state and thread._message_store is not None:
            await thread._message_store.update_from_state(chat_message_store_state, **kwargs)

        return thread

    async def update_from_thread_state(
        self,
        serialized_thread_state: MutableMapping[str, Any],
        **kwargs: Any,
    ) -> None:
        """Update the thread from serialized state data.

        :param serialized_thread_state: The serialized thread state as a dictionary.
        :type serialized_thread_state: MutableMapping[str, Any]
        """
        chat_message_store_state = serialized_thread_state.get("chat_message_store_state")
        if chat_message_store_state and self._message_store is not None:
            await self._message_store.update_from_state(chat_message_store_state, **kwargs)
