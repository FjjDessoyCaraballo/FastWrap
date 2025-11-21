from pydantic import BaseModel, Field
from typing import Optional
from dataclasses import dataclass

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
