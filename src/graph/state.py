from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

class DeviceConnection(BaseModel):
    """Thông tin kết nối thiết bị"""
    hostname: str = Field(default="")
    device_type: str = Field(default="cisco_ios")
    username: str = Field(default="")
    password: str = Field(default="")
    secret: Optional[str] = Field(default=None)
    port: int = Field(default=22)

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        extra = "ignore"

class NetworkState(MessagesState):
    """State cho network agent"""
    # Thông tin thiết bị
    target_device: Optional[DeviceConnection] = Field(default=None)
    devices: List[DeviceConnection] = Field(default_factory=list)
    
    # Dữ liệu thu thập
    command_outputs: Dict[str, str] = Field(default_factory=dict)
    running_config: Optional[str] = Field(default=None)
    interface_status: Dict[str, Any] = Field(default_factory=dict)
    vlan_info: Dict[str, Any] = Field(default_factory=dict)
    error_logs: List[str] = Field(default_factory=list)
    
    # Phân tích
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    root_cause: Optional[str] = Field(default=None)
    recommendations: List[str] = Field(default_factory=list)
    
    # Hành động
    actions_taken: List[str] = Field(default_factory=list)
    pending_actions: List[str] = Field(default_factory=list)
    
    # Kết quả
    final_report: Optional[str] = Field(default=None)
    incident_resolved: bool = Field(default=False)
    
    # Điều khiển luồng
    current_phase: str = Field(default="start")
    next_agent: Optional[str] = Field(default=None)

class Incident(BaseModel):
    """Mô hình sự cố"""
    id: str = Field(default="")
    description: str = Field(default="")
    severity: str = Field(default="")
    timestamp: str = Field(default="")
    status: str = Field(default="")
    affected_devices: List[str] = Field(default_factory=list)