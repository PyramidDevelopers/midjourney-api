from typing import Optional
from fastapi import UploadFile
from pydantic import BaseModel


class TriggerImagineIn(BaseModel):
    prompt: str
    extra: str
    picurl: Optional[str]

class TriggerConcept(BaseModel):
    concept_name:str
    concept_info:str


class TriggerUVIn(BaseModel):
    index: int
    msg_id: str
    msg_hash: str

    trigger_id: str  # 供业务定位触发ID，/trigger/imagine 接口返回的 trigger_id


class TriggerResetIn(BaseModel):
    msg_id: str
    msg_hash: str

    trigger_id: str  # 供业务定位触发ID，/trigger/imagine 接口返回的 trigger_id


class TriggerExpandIn(BaseModel):
    msg_id: str
    msg_hash: str
    direction: str  # right/left/up/down

    trigger_id: str  # 供业务定位触发ID，/trigger/imagine 接口返回的 trigger_id

class TriggerZoomOutIn(BaseModel):
    msg_id: str
    msg_hash: str
    zoomout: int    # 2x: 50; 1.5x: 75

    trigger_id: str  # 供业务定位触发ID，/trigger/imagine 接口返回的 trigger_id


class TriggerDescribeIn(BaseModel):
    upload_filename: str
    trigger_id: str


class QueueReleaseIn(BaseModel):
    trigger_id: str


class TriggerResponse(BaseModel):
    message: str = "success"
    trigger_id: str
    trigger_type: str = ""

class PromptResponse(BaseModel):
    message: str = "success"
    trigger_id: str
    trigger_type: str = ""
    additional_prompts: list[dict[str, str]] = []

class PromptErrorMsgIn(BaseModel):
    prev_msg: str
class PromptErrorMsgInResponse(BaseModel):
    message: str = "success"
    trigger_id: str
    trigger_type: str = ""
    prompt: str

class GenerateResponseIn(BaseModel):
    role: str
    question: str
class GenerateResponseOut(BaseModel):
    message: str = "success"
    trigger_id: str
    trigger_type: str = ""
    reply: str

class UploadResponse(BaseModel):
    message: str = "success"
    upload_filename: str = ""
    upload_url: str = ""
    trigger_id: str


class SendMessageIn(BaseModel):
    upload_filename: str


class SendMessageResponse(BaseModel):
    message: str = "success"
    picurl: str

class MessageBody(BaseModel):

    trigger_id: str  

class TableBody(BaseModel):

    data_type: str  
    msg_id : Optional[int]

class UploadBody(BaseModel):

    username : str
    user_id : str
    template : UploadFile