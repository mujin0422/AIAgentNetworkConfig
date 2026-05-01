from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from src.tools.network_connection import connect_to_device

@tool
def save_device_config(hostname: str) -> Dict[str, Any]:
    """LƯU CẤU HÌNH ĐANG CHẠY (RUNNING-CONFIG) VÀO BỘ NHỚ (STARTUP-CONFIG)."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        # Dùng send_command_timing vì lệnh write memory có thể mất vài giây để chạy xong
        output = connection.send_command_timing("write memory")
        connection.disconnect()
        
        return {"success": True, "device": hostname, "action": "save_config", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}