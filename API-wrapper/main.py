from fastapi import FastAPI, status
from pydantic import BaseModel, Field
from typing import Optional
import logging

app = FastAPI()
logger = logging.getLogger(__name__)
logging.basicConfig(filename='logfile.log', level=logging.INFO)

# Temporary JSON payload structure for ROLE endpoint. In the future we will need to add token parameters
class RoleRequest(BaseModel):
    agent_role: str = Field(..., min_length=1, description="The role of the agent")
    TTL: Optional[int] = Field(None, gt=0, description="Time to live in seconds")

class Completions(BaseModel):
    role: str = Field(..., min_length=1, description="Role to differentiate between chatbot and user")
    content: str = Field(..., min_length=1, description="Content of the message. Either user prompt or chatbot reply")

# NEED TO ADD TOKENIZED SECURITY LATER
@app.get("/")
async def root(status_code=status.HTTP_200_OK):
    logger.info("Received request at root")
    return ({ "Title": "VanaciPrime Chatbot Wrapper",
             "Version": "1.0.0.",
             "Author": "Felipe",
             "Status": "Development"})

@app.post("/role")
async def role(request: RoleRequest):
    try:
        logger.info(f"Received role request: {request.agent_role}, TTL: {request.TTL}")
    except Exception as e:
        logger.error(f"Error in processing role request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: Completions):
    return ({f"Role: {request.role} | Content: {request.content} "})
