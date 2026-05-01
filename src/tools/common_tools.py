import re
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
        output = connection.send_command_timing("write memory")
        connection.disconnect()
        
        return {"success": True, "device": hostname, "action": "save_config", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def get_running_config(hostname: str) -> Dict[str, Any]:
    """
    LẤY TOÀN BỘ CẤU HÌNH ĐANG CHẠY (RUNNING-CONFIG) CỦA THIẾT BỊ.
    Sử dụng lệnh này khi cần kiểm tra chi tiết cấu hình mà các lệnh show ngắn không cung cấp đủ.
    """
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command("show running-config", read_timeout=90)
        connection.disconnect()
        
        return {"success": True, "device": hostname, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def execute_show_command(command: str, hostname: str) -> Dict[str, Any]:
    """THỰC THI LỆNH SHOW BẤT KỲ TRÊN THIẾT BỊ CHỈ ĐỊNH."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command_timing(command, strip_prompt=False, strip_command=False)
        connection.disconnect()
        return {"success": True, "device": hostname, "command": command, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def ping_test(target_ip: str, source_hostname: str) -> Dict[str, Any]:
    """THỰC HIỆN LỆNH PING TỪ MỘT THIẾT BỊ NGUỒN ĐẾN IP ĐÍCH."""
    try:
        conn_res = connect_to_device(source_hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        ping_output = connection.send_command(f"ping {target_ip}", read_timeout=60)
        connection.disconnect() 
        
        success_rate = 0
        match = re.search(r"Success rate is (\d+) percent", ping_output)
        if match: 
            success_rate = int(match.group(1))
        
        return {
            "success": True, 
            "source": source_hostname, 
            "target": target_ip, 
            "success_rate": success_rate, 
            "output": ping_output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}