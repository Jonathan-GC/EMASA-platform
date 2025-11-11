from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List


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


class MeasurementConfig(BaseModel):
    id: int
    min: float
    max: float
    threshold: float
    unit: str


class DeviceMeasurementConfigs(BaseModel):
    dev_eui: str
    configs: List[MeasurementConfig]
    last_fetched: datetime
    last_updated: datetime


class DeviceMeasurementConfigsDB(DeviceMeasurementConfigs):
    id: str = Field(alias="_id")


class PendingAlert(BaseModel):
    dev_eui: str
    user_id: int
    alert_data: Dict[str, Any]
    created_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    last_retry_at: Optional[datetime] = None
    sent_via_websocket: bool = False
    error_message: Optional[str] = None


class PendingAlertDB(PendingAlert):
    id: str = Field(alias="_id")


class DeviceUserMapping(BaseModel):
    dev_eui: str
    tenant_id: str
    primary_user: int
    assigned_users: List[int]
    created_at: datetime
    updated_at: datetime


class DeviceUserMappingDB(DeviceUserMapping):
    id: str = Field(alias="_id")
