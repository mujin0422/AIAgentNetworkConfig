import yaml
from typing import Dict, Any
from netmiko import ConnectHandler
from core.config import settings

_CONNECTION_POOL = {}

def getDeviceConfig(device_identifier: str):
    try:
        with open("config/devices.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

            if device_identifier in config:
                return config[device_identifier]
                    
            return None 
    except Exception as e:
        print(f"Lỗi đọc config: {e}")
        return None

def connectToDevice(target: str) -> Dict[str, Any]:
    device_cfg = getDeviceConfig(target)
    if not device_cfg:
        return {"success": False, "error": f"Không tìm thấy cấu hình cho '{target}' trong devices.yaml"}
    
    connection_params = {
        'device_type': str(device_cfg.get("device_type", settings.DEFAULT_DEVICE_TYPE)), 
        'host': str(device_cfg.get("hostname", settings.DEFAULT_DEVICE_HOSTNAME)),
        'port': int(device_cfg.get("port", settings.DEFAULT_DEVICE_PORT)),
        'username': str(device_cfg.get("username", settings.DEFAULT_DEVICE_USERNAME)),
        'password': str(device_cfg.get("password", settings.DEFAULT_DEVICE_PASSWORD)),
        'secret': str(device_cfg.get("secret", "")), 
        'conn_timeout': int(settings.SSH_TIMEOUT),
        'auth_timeout': int(settings.SSH_AUTH_TIMEOUT),
        'global_delay_factor': float(settings.SSH_DELAY_FACTOR),
    }
    
    try:
        connection = ConnectHandler(**connection_params)
        if connection_params['secret'] and not connection.check_enable_mode():
            connection.enable()   
        return {"success": True, "device": target, "connection": connection}
    except Exception as e:
        return {"success": False, "device": target, "error": f"Kết nối thất bại: {str(e)}"}
