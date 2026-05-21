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

class UserRequest(BaseModel):
    email: str
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    email_enabled: Optional[bool] = True
    sms_enabled: Optional[bool] = True
    webhook_enabled: Optional[bool] = True
    preferred_channel: str

class UserResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    webhook_url: Optional[str]
    preferred_channel: str
    sms_enabled: bool
    email_enabled: bool
    webhook_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    is_active: Optional[bool] = None