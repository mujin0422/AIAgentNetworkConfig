import os
import time
from typing import Dict, Any, Optional, Callable
from netmiko import ConnectHandler
import yaml
from src.tools.parser_tools import *

_CONNECTION_POOL = {}

def execute_on_device(target: str, executor: Callable):
    started_at = time.perf_counter()
    conn_res = connect_to_device(target)
    if not conn_res["success"]:
        return conn_res

    connection = conn_res["connection"]
    try:
        result = executor(connection) or {}
        if not isinstance(result, dict):
            result = {"output": result}
        result.setdefault("success", True)
        result.setdefault("device", target)
        result["timings"] = {
            "total_seconds": round(time.perf_counter() - started_at, 3)
        }
        return result
    except Exception as e:
        return {"success": False, "device": target, "error": str(e)}

def get_ssh_params():
    return {
        'conn_timeout': int(os.getenv('SSH_TIMEOUT', 15)),
        'auth_timeout': int(os.getenv('SSH_AUTH_TIMEOUT', 15)),
        'global_delay_factor': float(os.getenv('SSH_DELAY_FACTOR', 1)),
    }

def get_device_config(device_identifier: str):
    try:
        with open("config/devices.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

            # Nếu truyền vào tên (P1, PE1...)
            if device_identifier in config:
                return config[device_identifier]
                
            # Nếu truyền vào địa chỉ IP
            for key, val in config.items():
                if val.get("hostname") == device_identifier:
                    return val
                    
            return None 
    except Exception as e:
        print(f"Lỗi đọc config: {e}")
        return None

def connect_to_device(target: str) -> Dict[str, Any]:
    device_cfg = get_device_config(target)
    if not device_cfg:
        return {"success": False, "error": f"Không tìm thấy cấu hình cho '{target}'"}
    
    target_host = str(device_cfg.get("hostname", ""))
    username = str(device_cfg.get("username", ""))
    password = str(device_cfg.get("password", ""))
    secret = str(device_cfg.get("secret", ""))
    port = int(device_cfg.get("port", 22))
    
    connection_params = {
        'device_type': str(device_cfg.get("device_type", "cisco_ios")), 
        'host': target_host,
        'username': username,
        'password': password,
        'secret': secret,
        'port': port,
        'session_timeout': int(os.getenv('SSH_SESSION_TIMEOUT', 15)),
        'fast_cli': os.getenv('SSH_FAST_CLI', 'true').lower() == 'true',
        **get_ssh_params()
    }
    
    try:
        pool_key = f"{target_host}:{port}:{username}"
        cached_connection = _CONNECTION_POOL.get(pool_key)

        if cached_connection is not None:
            try:
                cached_connection.find_prompt()
                return {"success": True, "connection": cached_connection}
            except Exception:
                try:
                    cached_connection.disconnect()
                except Exception:
                    pass
                _CONNECTION_POOL.pop(pool_key, None)
        connection = ConnectHandler(**connection_params)
        _CONNECTION_POOL[pool_key] = connection
        if secret and not connection.check_enable_mode():
            connection.enable()
        return {"success": True, "connection": connection}
    except Exception as e:
        return {"success": False, "error": str(e)}
