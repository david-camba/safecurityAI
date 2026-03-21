from pydantic import BaseModel, Field
from typing import Literal, Optional, Union

# ==========================================
# WEBSOCKET MESSAGES: SERVER -> CLIENT
# ==========================================


class BaseWSMessage(BaseModel):
    type: str = Field(..., description="Primary category of the message.")


class LogMessage(BaseWSMessage):
    type: Literal["log"] = "log"
    content: str


class ErrorMessage(BaseWSMessage):
    type: Literal["error"] = "error"
    content: str


class CompletionMessage(BaseWSMessage):
    type: Literal["complete"] = "complete"
    report: str


class ActionRequestBase(BaseWSMessage):
    type: Literal["action_request"] = "action_request"
    action_type: str
    message: str


class TextInputAction(ActionRequestBase):
    action_type: Literal["text_input"] = "text_input"


class FileUploadAction(ActionRequestBase):
    action_type: Literal["file_upload"] = "file_upload"
    target_path: Optional[str] = None


class ActionAcknowledgment(BaseWSMessage):
    type: Literal["action_ack"] = "action_ack"
    accepted_action: str


ServerActionRequest = Union[TextInputAction, FileUploadAction]
ServerMessage = Union[
    LogMessage,
    ErrorMessage,
    CompletionMessage,
    ActionAcknowledgment,
    ServerActionRequest,
]


# ==========================================
# WEBSOCKET MESSAGES: CLIENT -> SERVER
# ==========================================


class ClientResponseBase(BaseModel):
    type: str


class HumanTextResponse(ClientResponseBase):
    type: Literal["human_text_answer"] = "human_text_answer"
    answer: str = Field(..., min_length=1)


class HumanFileResponse(ClientResponseBase):
    type: Literal["human_file_upload"] = "human_file_upload"
    file_name: str
    file_content_base64: str


ClientMessage = Union[HumanTextResponse, HumanFileResponse]
