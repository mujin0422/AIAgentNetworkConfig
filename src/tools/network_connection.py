import yaml
from typing import Dict, Any
from netmiko import ConnectHandler
from config import settings

def get_ssh_params():
    return {
        'conn_timeout': int(settings.SSH_TIMEOUT),
        'auth_timeout': int(settings.SSH_AUTH_TIMEOUT),
        'global_delay_factor': float(settings.SSH_DELAY_FACTOR),
    }

def get_device_config(device_identifier: str):
    try:
        with open("config/devices.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

            if device_identifier in config:
                return config[device_identifier]
                    
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
        **get_ssh_params()
    }
    
    try:
        connection = ConnectHandler(**connection_params)
        if secret and not connection.check_enable_mode():
            connection.enable()
        return {"success": True, "connection": connection}
    except Exception as e:
        return {"success": False, "error": str(e)}
