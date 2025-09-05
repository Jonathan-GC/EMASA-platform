from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class MessageIn(BaseModel):
    tenant_id: str
    device_id: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class MessageDB(MessageIn):
    id: str = Field(alias="_id")
    timestamp: datetime
