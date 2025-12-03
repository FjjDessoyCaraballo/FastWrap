from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from dataclasses import dataclass
import string

class RoleRequest(BaseModel):
    uuid: str = Field(..., min_length=36, description="Unique user ID.")
    agent_role: str = Field(..., min_length=1, description="The role of the agent.")
    TTL: Optional[int] = Field(None, gt=0, description="Time to live in seconds. Optional parameter")

class PatchRole(BaseModel):
    agent_role: str = Field(..., min_length=1, description="The role of the agent.")
    TTL: Optional[int] = Field(None, gt=0, description="Time to live in seconds. Optional parameter")

class Completions(BaseModel):
    uuid: str = Field(..., min_length=36, description="Unique user ID.")
    role: str = Field(..., min_length=1, description="Role to differentiate between chatbot and user.")
    content: str = Field(..., min_length=1, description="Content of the message. Either user prompt or chatbot reply.")

class ServiceRoleRequest(BaseModel):
    uuid: str = Field(..., min_length=36, description="Unique user ID that serves as a general identifier for users and clients")

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def password_policy(cls, v):
        if len(v) < 10:
            raise ValueError('Password must be at least 10 characters')

        if not any(char.islower() for char in v):
            raise ValueError('Must have at least one lowercase character')

        if not any(char.isupper() for char in v):
            raise ValueError('Must have at least one uppercase character')

        if not any(char.isdigit() for char in v):
            raise ValueError('Must contain at least a number')

        if not any(char in string.punctuation for char in v):
            raise ValueError('Must contain at least one special character')

        if any(char in string.whitespace for char in v):
            raise ValueError('Cannot use space, tabs, or any other whitespace characters')
        
        return v
        
class LoginRequest(BaseModel):
    email: str
    password: str
