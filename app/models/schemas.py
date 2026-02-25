from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from dataclasses import dataclass
import string

class ServiceRole(BaseModel):
    agent_role: str = Field(..., min_length=1, description="The role of the agent.")
    TTL: Optional[int] = Field(None, gt=0, description="Time to live in seconds. Optional parameter")

class Completions(BaseModel):
    uuid: str = Field(..., min_length=36, description="Unique user ID.")
    role: str = Field(..., min_length=1, description="Role to differentiate between chatbot and user.")
    content: str = Field(..., min_length=1, description="Content of the message. Either user prompt or chatbot reply.")

class AuthRequest(BaseModel):
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

class UpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

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

class VectorUpsertRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, description="Namespace for the snippet (e.g. memory, character)")
    entity_id: str = Field(..., min_length=36, description="UUID that identifies the entity this snippet belongs to")
    content: str = Field(..., min_length=1, description="Text content to embed and store")
    metadata: Optional[dict] = Field(None, description="Optional JSON metadata")

class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    entity_type: Optional[str] = Field(None, description="Optional filter by entity_type")

class AdminClientCreateRequest(AuthRequest):
    is_admin: bool = False
    is_active: bool = True
    subscription: str = "free"
    store_name: Optional[str] = None
    phone: Optional[str] = None

class AdminClientUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    subscription: Optional[str] = None
    store_name: Optional[str] = None
    phone: Optional[str] = None
    
    @field_validator("password")
    def password_policy(cls, v):
        if v is None:
            return v
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
        