from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from src.tools.gns3_tools import(
    get_topology_links,
    check_nodes_status,
    start_node
)
from src.tools.router_tools import (
    execute_show_command,
    ping_test,
    get_routing_table,
    get_interface_ip,
    get_ospf_neighbors, 
    config_interface_ip,
    config_ospf,          
    config_static_route,      
    config_mpls_ip_interface,
    config_router_sub_interface
)

from src.tools.switch_tools import (
    config_vlan,
    assign_vlan_access_port,
    assign_vlan_access_range,
    config_switch_trunk,
    get_vlan_switch_brief,
    get_trunk_interfaces
)

def create_network_expert():
    tools = [
        get_topology_links,
        check_nodes_status,
        start_node,
        execute_show_command,
        ping_test,
        get_routing_table,
        get_interface_ip,
        config_ospf,
        config_static_route,     
        config_interface_ip,     
        get_ospf_neighbors,
        config_mpls_ip_interface,
        config_router_sub_interface,
        config_vlan, 
        assign_vlan_access_port,
        assign_vlan_access_range,
        config_switch_trunk,
        get_vlan_switch_brief,
        get_trunk_interfaces
    ]
    
    system_prompt = """
    Bạn là Network Expert, chuyên gia vận hành và cấu hình mạng Cisco trong môi trường GNS3.

    NHIỆM VỤ CỦA BẠN:
    1. Trinh sát hạ tầng: Bắt đầu bằng 'get_topology_links' và 'check_nodes_status' để nắm rõ sơ đồ và trạng thái nguồn của thiết bị.
    2. Kiểm tra trạng thái: Sử dụng các lệnh show, ping để lấy thông tin IP, định tuyến, VLAN thực tế.
    3. Triển khai cấu hình (MỚI): Thực thi các lệnh tạo VLAN, Sub-interface, Trunking, OSPF, Static Route khi được người dùng hoặc Analyst yêu cầu.

    NGUYÊN TẮC HOẠT ĐỘNG:
    - [KIỂM TRA THIẾT BỊ]: Nếu người dùng yêu cầu thao tác trên một thiết bị KHÔNG TỒN TẠI...
    - [THỰC THI THEO KẾ HOẠCH]: Nếu người dùng yêu cầu "Thực hiện cấu hình đã đề xuất", bạn PHẢI tự động lướt lên phần tin nhắn phía trên, tìm đọc "Kế hoạch Triển khai" do Analyst vừa tạo ra, trích xuất đúng các tham số (IP, VLAN, OSPF...) và gọi các Tool tương ứng để cấu hình.
    - [QUAN TRỌNG] Các công cụ cấu hình (config_*) đã được tích hợp sẵn cơ chế hỏi ý kiến người dùng (Human-in-the-Loop). Hãy tự tin gọi Tool cấu hình ngay khi xác định được tham số cần thiết, không cần hỏi rào đón bằng text.
    - Cung cấp toàn bộ output thô của lệnh cho Analyst. Không tự kết luận nguyên nhân gốc rễ, hãy để Analyst làm việc đó.
    - Trình bày log sạch sẽ, phân tách rõ ràng theo từng thiết bị.
    """
    
    llm = ChatOllama(
        model="qwen3-vl:235b-cloud",
        temperature=0.1,
        base_url="http://localhost:11434",
        num_predict=1024,
    )
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt
    )
    return agent