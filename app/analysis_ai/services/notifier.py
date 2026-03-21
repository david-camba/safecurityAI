import logging
from abc import ABC, abstractmethod
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
import asyncio
import json

from app.analysis_ai.schemas import (
    LogMessage,
    TextInputAction,
    ErrorMessage,
    CompletionMessage,
    HumanTextResponse,
    ActionAcknowledgment,
)
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """
    Abstract contract for all external communication from the AI Workflow.
    Any injected notifier must implement these methods.
    """

    @abstractmethod
    async def send_log(self, message: str) -> None:
        pass

    @abstractmethod
    async def ask_human(self, question: str) -> str:
        pass

    @abstractmethod
    async def send_error(self, message: str) -> None:
        pass

    @abstractmethod
    async def send_completion(self, report: str) -> None:
        pass


class WebSocketNotifier(BaseNotifier):
    """Concrete implementation for real-time WebSocket streaming in FastAPI."""

    def __init__(self, websocket: WebSocket):
        self.ws = websocket

    async def send_log(self, message: str) -> None:
        await self.ws.send_json(LogMessage(content=message).model_dump())

    async def ask_human(self, question: str) -> str:
        """Requests a text response from the user via WebSocket."""
        # 1. Dispatch the request to the Frontend
        await self.ws.send_json(TextInputAction(message=question).model_dump())

        # 2. Wait until valid response
        while True:
            try:
                raw_data = await asyncio.wait_for(self.ws.receive_json(), timeout=300.0)
                validated_response = HumanTextResponse(**raw_data)
                logger.info(f"Human answered: {validated_response.answer}")

                # 3. Confirm the answer is valid to the client
                ack_msg = ActionAcknowledgment(accepted_action="human_text_answer")
                await self.ws.send_json(ack_msg.model_dump())

                return validated_response.answer

            except (json.JSONDecodeError, ValidationError) as e:
                error_msg = ErrorMessage(
                    content="Invalid payload format. Expected 'human_text_answer' with 'answer'."
                )
                await self.ws.send_json(error_msg.model_dump())
                logger.warning(f"Frontend invalid payload: {e.errors()}")

            except WebSocketDisconnect:
                logger.warning("Client disconnected during human interaction.")
                raise

            except Exception as e:
                logger.error(f"Critical socket read error: {e}")
                return "No response."

    async def send_error(self, message: str) -> None:
        await self.ws.send_json(ErrorMessage(content=message).model_dump())

    async def send_completion(self, report: str) -> None:
        await self.ws.send_json(CompletionMessage(report=report).model_dump())


class VoidNotifier(BaseNotifier):
    """
    Silent implementation for background processes, unit testing,
    or scenarios where no human interaction is available.
    """

    async def send_log(self, message: str) -> None:
        pass  # Intentionally swallows logs

    async def ask_human(self, question: str) -> str:
        # Prevents tools from hanging or failing if they expect a string response
        logger.warning(f"VoidNotifier swallowed human request: {question}")
        return "[AUTOMATED EXECUTION: No human available to answer. Proceed with default assumptions.]"

    async def send_error(self, message: str) -> None:
        pass

    async def send_completion(self, report: str) -> None:
        pass
