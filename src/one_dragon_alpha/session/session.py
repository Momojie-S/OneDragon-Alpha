import asyncio
from typing import Any, AsyncGenerator

from agentscope.agent import AgentBase
from agentscope.memory import MemoryBase
from agentscope.message import Msg

from one_dragon_alpha.session.session_message import SessionMessage


class Session:
    """Chat session management with streaming response processing.

    This class manages chat sessions and provides methods for processing
    chat messages with streaming response support using hooks.

    Attributes:
        agent: The agent instance for processing chat messages.
        session_id: Unique identifier for the session.
        memory: Memory instance for storing conversation history.
        response_queue: Async queue for storing response chunks.
    """

    def __init__(
        self,
        session_id: str,
        agent: AgentBase,
        memory: MemoryBase
    ):
        """Initialize the session.

        Args:
            session_id: Unique identifier for the session.
            agent: The agent instance for processing chat messages.
            memory: Memory instance for storing conversation history.
        """
        self.session_id: str = session_id
        self.agent: AgentBase = agent
        self.memory: MemoryBase = memory
        self.response_queue: asyncio.Queue = asyncio.Queue()

        # Bind hooks in constructor
        self.agent.register_instance_hook(
            hook_type="pre_print",
            hook_name="chat_capture",
            hook=self._pre_print_hook,
        )

    async def _put_chunk(self, msg: SessionMessage) -> None:
        """Put a response chunk into the queue.

        Args:
            msg: The message chunk to be queued.
        """
        await self.response_queue.put(msg)

    async def _get_chunk(self) -> SessionMessage:
        """Get a response chunk from the queue.

        Returns:
            A SessionMessage containing response chunk.
        """
        return await self.response_queue.get()

    async def _pre_print_hook(self, agent_instance: AgentBase, kwargs: dict[str, Any]) -> dict[str, Any] | None:
        """Pre-print hook to capture agent output in real-time.

        This hook is called before agent prints its output, allowing
        us to capture and queue response chunks for streaming.

        Args:
            agent_instance: The agent instance generating output.
            kwargs: Dictionary containing hook parameters.

        Returns:
            None to not modify original arguments.
        """
        msg: Msg = kwargs.get("msg")
        is_last = kwargs.get("last", False)

        await self._put_chunk(SessionMessage(msg, is_last, False))

        return None

    def _on_response_completed(self, task: asyncio.Task) -> None:
        """Callback when agent response processing is completed.

        Args:
            task: The completed agent task.
        """
        try:
            task.result()
            asyncio.create_task(self._put_chunk(SessionMessage(None, False, True)))
        except asyncio.CancelledError:
            print("Task was cancelled")
        except Exception as e:
            print(f"Task failed with exception: {e}")

    async def chat(self, user_input: str) -> AsyncGenerator[SessionMessage, None]:
        """Process a chat message and yield streaming responses.

        This method processes a user input message and yields SessionMessage
        objects as the agent generates responses in real-time.

        Args:
            user_input: The user's message content.

        Yields:
            SessionMessage objects containing response chunks and completion status.
        """
        try:
            msg = Msg(name="user", content=user_input, role="user")
            agent_task = asyncio.create_task(self.agent(msg))
            agent_task.add_done_callback(self._on_response_completed)

            while True:
                msg = await self._get_chunk()

                yield msg

                if msg.response_completed:
                    break

            if not agent_task.done():
                await agent_task

        except Exception as e:
            yield SessionMessage(
                msg=Msg(name=self.agent.id, content=str(e), role="system"),
                message_completed=False,
                response_completed=True
            )

    async def interrupt(self) -> None:
        """Interrupt the current agent processing.

        This method interrupts the agent's current processing task.
        """
        await self.agent.interrupt()
