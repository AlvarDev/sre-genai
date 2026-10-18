from pydantic import BaseModel, Field

from validation import MAX_MESSAGE_CHARS

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    session_id: str

class ChatResponse(BaseModel):
    text: str
    session_id: str
    products: list = []
