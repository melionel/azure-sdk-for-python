# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
from typing import Optional, Union

from agent_framework import AgentThread, AgentProtocol, WorkflowAgent

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential

from .agent_thread_repository import AgentThreadRepository
from ._foundry_conversation_agent_thread import FoundryConversationAgentThread


class FoundryConversationThreadRepository(AgentThreadRepository):
    """An AgentThreadRepository implementation that manages FoundryConversationAgentThread instances.

    This repository creates and manages agent threads that use the Azure AI Foundry
    Conversations API for message storage. Each thread is associated with a conversation_id.

    :param project_endpoint: The Azure AI Foundry project endpoint.
    :type project_endpoint: str
    :param credentials: The token credential for authentication.
    :type credentials: Union[TokenCredential, AsyncTokenCredential]
    """

    def __init__(
        self,
        project_endpoint: str,
        credentials: Union[TokenCredential, AsyncTokenCredential],
    ) -> None:
        """Initialize the FoundryConversationThreadRepository.

        :param project_endpoint: The Azure AI Foundry project endpoint.
        :type project_endpoint: str
        :param credentials: The token credential for authentication.
        :type credentials: Union[TokenCredential, AsyncTokenCredential]
        """
        self._project_endpoint = project_endpoint
        self._credentials = credentials
        self._threads: dict[str, FoundryConversationAgentThread] = {}

    async def get(
        self,
        conversation_id: Optional[str],
        agent: Optional[Union[AgentProtocol, WorkflowAgent]] = None,
    ) -> Optional[AgentThread]:
        """Retrieve or create a thread for a given conversation ID.

        If a thread for the conversation_id already exists in the cache, it is returned.
        Otherwise, a new FoundryConversationAgentThread is created.

        :param conversation_id: The conversation ID.
        :type conversation_id: Optional[str]
        :param agent: The agent instance (not used in this implementation).
        :type agent: Optional[Union[AgentProtocol, WorkflowAgent]]
        :return: The AgentThread for the conversation, or None if conversation_id is None.
        :rtype: Optional[AgentThread]
        """
        if not conversation_id:
            return None

        if conversation_id in self._threads:
            return self._threads[conversation_id]

        thread = FoundryConversationAgentThread(
            conversation_id=conversation_id,
            project_endpoint=self._project_endpoint,
            credentials=self._credentials,
        )
        self._threads[conversation_id] = thread
        return thread

    async def set(self, conversation_id: Optional[str], thread: AgentThread) -> None:
        """Store a thread for a given conversation ID.

        Note: Messages are managed externally by the Foundry Conversations API,
        so this method only updates the internal thread cache.

        :param conversation_id: The conversation ID.
        :type conversation_id: Optional[str]
        :param thread: The thread to store.
        :type thread: AgentThread
        """
        if not conversation_id or not thread:
            return

        if isinstance(thread, FoundryConversationAgentThread):
            self._threads[conversation_id] = thread
