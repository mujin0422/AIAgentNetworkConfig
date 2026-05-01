import os
from typing import Dict, Any, Optional
from netmiko import ConnectHandler
import yaml
from src.tools.parser_tools import *

def get_ssh_params():
    """Lấy tham số SSH từ môi trường"""
    return {
        'conn_timeout': int(os.getenv('SSH_TIMEOUT', 60)),
        'auth_timeout': int(os.getenv('SSH_AUTH_TIMEOUT', 30)),
        'global_delay_factor': float(os.getenv('SSH_DELAY_FACTOR', 2)),
    }

def get_device_config(device_identifier: str):
    """
    Đọc config thiết bị từ file yaml dựa vào tên (VD: 'P1') hoặc IP (VD: '10.0.0.1').
    """
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
    
    # Đã sửa lỗi ghi đè biến ở đây
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
        'session_timeout': 15,
        'fast_cli': False,
        **get_ssh_params()
    }
    
    try:
        connection = ConnectHandler(**connection_params)
        if secret and not connection.check_enable_mode():
            connection.enable()
        return {"success": True, "connection": connection}
    except Exception as e:
        return {"success": False, "error": str(e)}
