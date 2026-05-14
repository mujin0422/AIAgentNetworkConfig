import re
from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from src.tools.network_connection import connect_to_device
from src.tools.network_connection import execute_on_device

@tool
def save_device_config(hostname: str) -> Dict[str, Any]:
    """LƯU CẤU HÌNH ĐANG CHẠY (RUNNING-CONFIG) VÀO BỘ NHỚ (STARTUP-CONFIG)."""
    try:
        return execute_on_device(
            hostname,
            lambda connection: {
            "output": connection.send_command_timing("write memory"),
            "action": "save_config",
            },
        )
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def get_running_config(hostname: str) -> Dict[str, Any]:
    """
    LẤY TOÀN BỘ CẤU HÌNH ĐANG CHẠY (RUNNING-CONFIG) CỦA THIẾT BỊ.
    Sử dụng lệnh này khi cần kiểm tra chi tiết cấu hình mà các lệnh show ngắn không cung cấp đủ.
    """
    try:
        return execute_on_device(
            hostname,
            lambda connection: {
                "output": connection.send_command("show running-config", read_timeout=90),
                "command": "show running-config",
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def execute_show_command(command: str, hostname: str) -> Dict[str, Any]:
    """THỰC THI LỆNH SHOW BẤT KỲ TRÊN THIẾT BỊ CHỈ ĐỊNH."""
    try:
        return execute_on_device(
            hostname,
            lambda connection: {
                "output": connection.send_command_timing(command, strip_prompt=False, strip_command=False),
                "command": command,
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def ping_test(target_ip: str, source_hostname: str) -> Dict[str, Any]:
    """THỰC HIỆN LỆNH PING TỪ MỘT THIẾT BỊ NGUỒN ĐẾN IP ĐÍCH."""
    try:
        result = execute_on_device(
            source_hostname,
            lambda connection: {
                "output": connection.send_command(f"ping {target_ip}", read_timeout=60),
                "target": target_ip,
            }
        )

        if not result["success"]:
            return result

        ping_output = result.get("output", "")
        success_rate = 0
        match = re.search(r"Success rate is (\d+) percent", ping_output)
        if match:
            success_rate = int(match.group(1))

        return {
            "success": True,
            "source": source_hostname,
            "target": target_ip,
            "success_rate": success_rate,
            "output": ping_output,
            "timings": result.get("timings")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}