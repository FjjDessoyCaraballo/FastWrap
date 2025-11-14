from pydantic import BaseModel, Field
from typing import Optional

# Temporary JSON payload structure for ROLE endpoint. In the future we will need to add token parameters

class RoleRequest(BaseModel):
    agent_role: str = Field(..., min_length=1, description="The role of the agent")
    TTL: Optional[int] = Field(None, gt=0, description="Time to live in seconds")

class Completions(BaseModel):
    role: str = Field(..., min_length=1, description="Role to differentiate between chatbot and user")
    content: str = Field(..., min_length=1, description="Content of the message. Either user prompt or chatbot reply")

