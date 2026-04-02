import yaml
from typing import Dict, Any

def load_device_config(path: str = "config/devices.yaml") -> Dict[str, Any]:
    """
    Load cấu hình thiết bị từ file YAML.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise Exception(f"Không tìm thấy file config: {path}")
    except Exception as e:
        raise Exception(f"Lỗi khi load config: {str(e)}")