from pydantic import BaseModel, ConfigDict
from  typing import Optional
from datetime import datetime

# TemplateCreate 
class TemplateCreate(BaseModel):
    name: str
    subject: Optional[str]
    body: str
    channel: str
# TemplateResponse
class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: Optional[str] 
    body: str
    channel: str 
    created_at: datetime 
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# RenderResponse
class RenderResponse(BaseModel):
    rendered_subject: Optional[str]
    rendered_body: str

# RenderRequest
class RenderRequest(BaseModel):
    variables: dict

class NotificationRequest(BaseModel):
    user_id: int
    template_id: int
    variables: dict
    priority: Optional[str] = "normal"
    channel: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    template_id: int
    channel: Optional[str]
    subject: Optional[str]
    body: str
    priority: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)