from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from src.tools.network_connection import connect_to_device

@tool
def config_vlan(hostname: str, vlan_id: str, vlan_name: str = "") -> Dict[str, Any]:
    """TẠO VÀ CẤU HÌNH VLAN TRÊN SWITCH/ROUTER."""
    action_msg = f"Tạo VLAN {vlan_id} (Tên: {vlan_name if vlan_name else 'Mặc định'}) trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}    
    
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [f"vlan {vlan_id}"]
        if vlan_name: config_commands.append(f"name {vlan_name}") 
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        return {"success": True, "device": hostname, "action": "config_vlan", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def assign_vlan_access_port(hostname: str, interface: str, vlan_id: str) -> Dict[str, Any]:
    """GÁN MỘT CỔNG (INTERFACE) VÀO VLAN CỤ THỂ Ở CHẾ ĐỘ ACCESS. """
    action_msg = f"Cấu hình cổng {interface} thành Access Port và gán vào VLAN {vlan_id} trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"interface {interface}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "no shutdown"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {"success": True, "device": hostname, "action": "assign_vlan_access", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def assign_vlan_access_range(hostname: str, interface_range: str, vlan_id: str) -> Dict[str, Any]:
    """GÁN MỘT DẢI CỔNG (INTERFACE RANGE) VÀO VLAN CỤ THỂ Ở CHẾ ĐỘ ACCESS."""
    action_msg = f"Cấu hình HÀNG LOẠT cổng [{interface_range}] thành Access Port và gán vào VLAN {vlan_id} trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"interface range {interface_range}",
            "switchport mode access",
            f"switchport access vlan {vlan_id}",
            "no shutdown"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {"success": True, "device": hostname, "action": "assign_vlan_access_range", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
        
@tool
def config_switch_trunk(hostname: str, interface: str, allowed_vlans: str = "all") -> Dict[str, Any]:
    """CẤU HÌNH MỘT CỔNG THÀNH ĐƯỜNG TRUNK ĐỂ CHO PHÉP NHIỀU VLAN ĐI QUA. """
    action_msg = f"Cấu hình cổng {interface} thành đường TRUNK (Cho phép VLAN: {allowed_vlans}) trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"interface {interface}",
            "switchport trunk encapsulation dot1q",
            "switchport mode trunk",
            f"switchport trunk allowed vlan {allowed_vlans}",
            "no shutdown"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {
            "success": True, 
            "device": hostname, 
            "action": "config_switch_trunk", 
            "output": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
            
@tool
def get_vlan_switch_brief(hostname: str) -> Dict[str, Any]:
    """XEM THÔNG TIN CÁC VLAN ĐANG CÓ TRÊN THIẾT BỊ."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command_timing("show vlan-switch brief")
        connection.disconnect()
        
        return {"success": True, "device": hostname, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def get_trunk_interfaces(hostname: str) -> Dict[str, Any]:
    """XEM THÔNG TIN CÁC CỔNG TRUNK ĐANG CÓ TRÊN THIẾT BỊ."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command_timing("show interface trunk")
        connection.disconnect()
        
        return {"success": True, "device": hostname, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}