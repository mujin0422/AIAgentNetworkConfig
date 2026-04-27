import re
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

# @tool
# def config_ospf(hostname: str, process_id: str, network: str, wildcard_mask: str, area: str) -> Dict[str, Any]:
#     """
#     CẤU HÌNH ĐỊNH TUYẾN OSPF TRÊN THIẾT BỊ.
#     Args:
#         hostname: Tên thiết bị cần cấu hình (VD: "P1").
#         process_id: ID của tiến trình OSPF (VD: "1").
#         network: Địa chỉ mạng cần quảng bá (VD: "10.0.0.0").
#         wildcard_mask: Wildcard mask của mạng (VD: "0.0.0.255").
#         area: Khu vực OSPF (VD: "0").
#     """
#     try:
#         conn_res = connect_to_device(hostname)
#         if not conn_res["success"]: return conn_res

#         connection = conn_res["connection"]
        
#         # Tập hợp các lệnh cấu hình
#         config_commands = [
#             f"router ospf {process_id}",
#             f"network {network} {wildcard_mask} area {area}"
#         ]
        
#         # send_config_set tự động vào/ra mode 'configure terminal'
#         output = connection.send_config_set(config_commands)
#         connection.disconnect()
        
#         return {"success": True, "device": hostname, "action": "config_ospf", "output": output}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# @tool
# def config_static_route(hostname: str, destination: str, subnet_mask: str, next_hop: str) -> Dict[str, Any]:
#     """
#     CẤU HÌNH ĐỊNH TUYẾN TĨNH (STATIC ROUTE) TRÊN THIẾT BỊ.
#     Args:
#         hostname: Tên thiết bị cần cấu hình (VD: "P1").
#         destination: Mạng đích cần đến (VD: "192.168.2.0" hoặc "0.0.0.0" cho default route).
#         subnet_mask: Subnet mask của mạng đích (VD: "255.255.255.0" hoặc "0.0.0.0").
#         next_hop: Địa chỉ IP trạm kế tiếp hoặc cổng ra (VD: "10.0.0.2" hoặc "FastEthernet0/0").
#     """
#     try:
#         conn_res = connect_to_device(hostname)
#         if not conn_res["success"]: return conn_res

#         connection = conn_res["connection"]
        
#         config_commands = [
#             f"ip route {destination} {subnet_mask} {next_hop}"
#         ]
        
#         output = connection.send_config_set(config_commands)
#         connection.disconnect()
        
#         return {"success": True, "device": hostname, "action": "config_static_route", "output": output}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# @tool
# def config_vlan(hostname: str, vlan_id: str, vlan_name: str = "") -> Dict[str, Any]:
#     """
#     TẠO VÀ CẤU HÌNH VLAN TRÊN SWITCH/ROUTER.
#     Args:
#         hostname: Tên thiết bị (VD: "Switch1").
#         vlan_id: Số ID của VLAN (VD: "10").
#         vlan_name: Tên của VLAN (Optional, VD: "HR_DEPT").
#     """
#     try:
#         conn_res = connect_to_device(hostname)
#         if not conn_res["success"]: return conn_res

#         connection = conn_res["connection"]
        
#         config_commands = [f"vlan {vlan_id}"]
#         if vlan_name:
#             config_commands.append(f"name {vlan_name}")
            
#         output = connection.send_config_set(config_commands)
#         connection.disconnect()
        
#         return {"success": True, "device": hostname, "action": "config_vlan", "output": output}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

@tool
def config_ospf(hostname: str, process_id: str, network: str, wildcard_mask: str, area: str) -> Dict[str, Any]:
    """CẤU HÌNH ĐỊNH TUYẾN OSPF TRÊN THIẾT BỊ."""
    try:
        action_msg = f"Cấu hình OSPF (Process: {process_id}, Network: {network} {wildcard_mask}, Area: {area}) trên {hostname}."
        user_approval = interrupt(action_msg) 
        
        if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
            return {"success": False, "error": "Đã hủy bởi người dùng."}

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
    try:
        action_msg = f"Tạo Static Route đến {destination}/{subnet_mask} qua Next-hop {next_hop} trên {hostname}."
        user_approval = interrupt(action_msg)
        
        if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
            return {"success": False, "error": "Đã hủy bởi người dùng."}

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
def config_router_sub_interface(hostname: str, main_interface: str, sub_int_number: str, vlan_id: str, ip_address: str, subnet_mask: str) -> Dict[str, Any]:
    """
    CẤU HÌNH SUB-INTERFACE TRÊN ROUTER ĐỂ HỖ TRỢ INTER-VLAN ROUTING (ROUTER-ON-A-STICK).
    Args:
        hostname: Tên Router cần cấu hình (VD: "P1").
        main_interface: Tên cổng vật lý gốc (VD: "FastEthernet0/0").
        sub_int_number: Số hiệu sub-interface (VD: "10").
        vlan_id: ID của VLAN cần định tuyến (VD: "10").
        ip_address: IP Gateway cho VLAN đó (VD: "192.168.10.1").
        subnet_mask: Subnet mask tương ứng (VD: "255.255.255.0").
    """
    try:
        # 1. Chốt chặn bảo mật (HITL)
        action_msg = f"Cấu hình Sub-interface {main_interface}.{sub_int_number} cho VLAN {vlan_id} với IP {ip_address} trên {hostname}."
        user_approval = interrupt(action_msg)
        
        if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
            return {"success": False, "error": "Đã hủy bởi người dùng."}

        # 2. Thực thi kết nối và cấu hình
        conn_res = connect_to_device(hostname)
        if not conn_res["success"]: return conn_res

        connection = conn_res["connection"]
        
        # Tập hợp các lệnh cấu hình Sub-interface
        config_commands = [
            f"interface {main_interface}.{sub_int_number}",
            f"encapsulation dot1Q {vlan_id}",
            f"ip address {ip_address} {subnet_mask}",
            "no shutdown",
            f"interface {main_interface}", # Đảm bảo cổng vật lý cũng được bật
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