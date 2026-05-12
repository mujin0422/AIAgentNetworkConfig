import requests
from langchain_core.tools import tool
from langgraph.types import interrupt
from core.connection import GNS3_URL_LINKS, GNS3_URL_NODES

@tool
def get_topology_links() -> str:
    """Lấy thông tin kết nối chi tiết: Tên thiết bị và cổng tương ứng trong GNS3."""
    try:
        # 1. Lấy danh sách tất cả các node để tạo bảng ánh xạ ID -> Name
        # Giả định GNS3_URL_NODES là URL đến project nodes (ví dụ: .../nodes)
        node_res = requests.get(GNS3_URL_NODES)
        node_res.raise_for_status()
        nodes_list = node_res.json()
        
        # Tạo dictionary mapping: {node_id: name}
        node_map = {n['node_id']: n['name'] for n in nodes_list}

        # 2. Lấy danh sách các link
        link_res = requests.get(GNS3_URL_LINKS)
        link_res.raise_for_status()
        links = link_res.json()
        
        if not links:
            return "Không tìm thấy kết nối nào."

        output = "SƠ ĐỒ KẾT NỐI CHI TIẾT (TOPOLOGY):\n"
        for link in links:
            n = link['nodes']
            
            id_a = n[0]['node_id']
            name_a = node_map.get(id_a, f"Unknown({id_a[:5]})")
            port_a = n[0]['label'].get('text', f"Port {n[0]['port_number']}")

            id_b = n[1]['node_id']
            name_b = node_map.get(id_b, f"Unknown({id_b[:5]})")
            port_b = n[1]['label'].get('text', f"Port {n[1]['port_number']}")

            output += f"- {name_a} ({port_a}) <---> {name_b} ({port_b})\n"
            
        return output
    except Exception as e:
        return f"Lỗi lấy links: {str(e)}"

@tool
def check_nodes_status() -> str:
    """Kiểm tra trạng thái của tất cả thiết bị trong GNS3 và trả về báo cáo chi tiết."""
    try:
        response = requests.get(GNS3_URL_NODES)
        response.raise_for_status()
        nodes = response.json()
        
        output = "TRẠNG THÁI THIẾT BỊ:\n"
        for node in nodes:
            output += f"- {node['name']}: {node['status']}\n"
        return output
    except Exception as e:
        return f"Lỗi lấy trạng thái node: {str(e)}"
    
@tool
def start_node(node_name: str) -> str:
    """Sử dụng công cụ này để bật nguồn (start) một thiết bị trong GNS3 khi nó đang ở trạng thái 'stopped'."""
    try:
        nodes_resp = requests.get(GNS3_URL_NODES)
        nodes = nodes_resp.json()
        node_id = next((n['node_id'] for n in nodes if n['name'] == node_name), None)
        
        if not node_id:
            return f"Không tìm thấy thiết bị có tên {node_name} để bật."

        url_start = f"{GNS3_URL_NODES}/{node_id}/start"
        response = requests.post(url_start)
        if response.status_code in [200, 201, 204]:
            return f"Đã gửi lệnh khởi động thiết bị {node_name} thành công. Vui lòng đợi vài giây để thiết bị khởi động xong."
        else:
            return f"Không thể bật thiết bị {node_name}. Lỗi: {response.text}"
    except Exception as e:
        return f"Lỗi hệ thống khi cố gắng bật thiết bị: {str(e)}"
    
@tool
def stop_node(node_name: str) -> str:
    """TẮT NGUỒN (STOP) MỘT THIẾT BỊ TRONG GNS3. Chỉ sử dụng khi cần mô phỏng lỗi phần cứng hoặc theo yêu cầu cụ thể."""
    action_msg = f"CẢNH BÁO: Tắt nguồn (Stop) thiết bị {node_name} trên GNS3."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return "Đã hủy thao tác tắt nguồn bởi người dùng."
    
    try:
        nodes_resp = requests.get(GNS3_URL_NODES)
        nodes = nodes_resp.json()
        node_id = next((n['node_id'] for n in nodes if n['name'] == node_name), None)
        
        if not node_id:
            return f"Không tìm thấy thiết bị có tên {node_name} để tắt."

        url_stop = f"{GNS3_URL_NODES}/{node_id}/stop"
        response = requests.post(url_stop)
        if response.status_code in [200, 201, 204]:
            return f"Đã tắt nguồn thiết bị {node_name} thành công."
        else:
            return f"Không thể tắt thiết bị {node_name}. Lỗi: {response.text}"
    except Exception as e:
        return f"Lỗi hệ thống khi cố gắng restart thiết bị: {str(e)}"

@tool
def restart_node(node_name: str) -> str:
    """KHỞI ĐỘNG LẠI (RESTART/RELOAD) MỘT THIẾT BỊ TRONG GNS3."""
    action_msg = f"CẢNH BÁO: Khởi động lại (Restart) thiết bị {node_name} trên GNS3."
    user_approval = interrupt(action_msg)
        
    if str(user_approval).lower() not in ['y', 'yes', 'ok', 'có', 'co']:
        return "Đã hủy thao tác khởi động lại bởi người dùng."
    
    try:
        nodes_resp = requests.get(GNS3_URL_NODES)
        nodes = nodes_resp.json()
        node_id = next((n['node_id'] for n in nodes if n['name'] == node_name), None)
        
        if not node_id:
            return f"Không tìm thấy thiết bị có tên {node_name} để restart."

        url_stop = f"{GNS3_URL_NODES}/{node_id}/stop"
        url_start = f"{GNS3_URL_NODES}/{node_id}/start"
        
        requests.post(url_stop)
        import time
        time.sleep(2) 
        response = requests.post(url_start)
        
        if response.status_code in [200, 201, 204]:
            return f"Đã gửi lệnh khởi động lại thiết bị {node_name}. Vui lòng chờ thiết bị boot xong."
        else:
            return f"Lỗi trong quá trình khởi động lại {node_name}: {response.text}"
    except Exception as e:
        return f"Lỗi hệ thống khi cố gắng restart thiết bị: {str(e)}"