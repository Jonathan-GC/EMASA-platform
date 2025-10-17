from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class MessageIn(BaseModel):
    tenant_id: str
    tenant_name: Optional[str] = None
    dev_eui: str
    dev_addr: Optional[str] = None
    device_name: Optional[str] = None
    frequency: Optional[int] = None
    f_cnt: Optional[int] = None
    region: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class MessageDB(MessageIn):
    id: str = Field(alias="_id")
    timestamp: datetime
