from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from src.tools.network_connection import connect_to_device
from src.tools.parser_tools import parse_interface_ip

@tool
def get_interface_ip(hostname: str) -> Dict[str, Any]:
    """LẤY ĐỊA CHỈ IP TRÊN TẤT CẢ CÁC INTERFACE CỦA MỘT THIẾT BỊ."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command_timing("show ip interface brief")
        connection.disconnect() 
        
        try:
            interfaces = parse_interface_ip(output)
        except Exception:
            interfaces = {}
               
        return {"success": True, "device": hostname, "interfaces": interfaces, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def get_routing_table(hostname: str) -> Dict[str, Any]:
    """LẤY BẢNG ĐỊNH TUYẾN CỦA ROUTER CỤ THỂ."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        routing_table = connection.send_command_timing("show ip route")
        connection.disconnect()
        return {"success": True, "device": hostname, "output": routing_table}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def get_ospf_neighbors(hostname: str) -> Dict[str, Any]:
    """KIỂM TRA DANH SÁCH LÁNG GIỀNG OSPF."""
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        output = connection.send_command_timing("show ip ospf neighbor")
        connection.disconnect()
        
        return {"success": True, "device": hostname, "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def config_interface_ip(hostname: str, interface: str, ip_address: str, subnet_mask: str) -> Dict[str, Any]:
    """CẤU HÌNH ĐỊA CHỈ IP CHO MỘT CỔNG (INTERFACE) CỦA ROUTER."""
    action_msg = f"Cấu hình IP {ip_address} {subnet_mask} cho cổng {interface} trên thiết bị {hostname} và bật cổng (no shutdown)."
    user_approval = interrupt(action_msg)

    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"interface {interface}",
            f"ip address {ip_address} {subnet_mask}",
            "no shutdown"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {
            "success": True, 
            "device": hostname, 
            "action": "config_interface_ip", 
            "output": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool
def config_ospf(hostname: str, process_id: str, network: str, wildcard_mask: str, area: str) -> Dict[str, Any]:
    """CẤU HÌNH ĐỊNH TUYẾN OSPF TRÊN THIẾT BỊ."""        
    action_msg = f"Cấu hình OSPF (Process: {process_id}, Network: {network} {wildcard_mask}, Area: {area}) trên {hostname}."
    user_approval = interrupt(action_msg) 
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"router ospf {process_id}",
            f"network {network} {wildcard_mask} area {area}"
        ]
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        return {"success": True, "device": hostname, "action": "config_ospf", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}

@tool
def config_static_route(hostname: str, destination: str, subnet_mask: str, next_hop: str) -> Dict[str, Any]:
    """CẤU HÌNH ĐỊNH TUYẾN TĨNH (STATIC ROUTE) TRÊN THIẾT BỊ."""
    action_msg = f"Tạo Static Route đến {destination}/{subnet_mask} qua Next-hop {next_hop} trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}
    
    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [f"ip route {destination} {subnet_mask} {next_hop}"]
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        return {"success": True, "device": hostname, "action": "config_static_route", "output": output}
    except Exception as e:
        return {"success": False, "error": str(e)}
   
@tool
def config_mpls_ip_interface(hostname: str, interface: str) -> Dict[str, Any]:
    """KÍCH HOẠT CHỨC NĂNG MPLS TRÊN MỘT CỔNG (INTERFACE) CỦA ROUTER."""        
    action_msg = f"Kích hoạt giao thức MPLS (lệnh 'mpls ip') trên cổng {interface} của thiết bị {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}

    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        config_commands = [
            f"interface {interface}",
            "mpls ip"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {
            "success": True, 
            "device": hostname, 
            "action": "config_mpls_ip_interface", 
            "output": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
        
@tool
def config_router_sub_interface(hostname: str, main_interface: str, sub_int_number: str, vlan_id: str, ip_address: str, subnet_mask: str) -> Dict[str, Any]:
    """CẤU HÌNH SUB-INTERFACE TRÊN ROUTER ĐỂ HỖ TRỢ INTER-VLAN ROUTING (ROUTER-ON-A-STICK)."""
    action_msg = f"Cấu hình Sub-interface {main_interface}.{sub_int_number} cho VLAN {vlan_id} với IP {ip_address} trên {hostname}."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return {"success": False, "error": "Đã hủy bởi người dùng."}

    try:
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        
        config_commands = [
            f"interface {main_interface}.{sub_int_number}",
            f"encapsulation dot1Q {vlan_id}",
            f"ip address {ip_address} {subnet_mask}",
            f"interface {main_interface}",
            "no shutdown"
        ]
            
        output = connection.send_config_set(config_commands)
        connection.disconnect()
        
        return {
            "success": True, 
            "device": hostname, 
            "action": "config_sub_interface", 
            "output": output
        }
    except Exception as e:
        return {"success": False, "error": str(e)}    