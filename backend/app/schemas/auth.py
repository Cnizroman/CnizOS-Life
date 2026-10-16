from pydantic import BaseModel, Field
from typing import Optional

class SetupRequest(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$", max_length=320)
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = Field(default="Owner", max_length=200)

class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$", max_length=320)
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    timezone: str
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    token_type: str = "bearer"

class SetupStatusOut(BaseModel):
    setup_required: bool
