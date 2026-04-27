import os
import yaml
import requests
import json
import logging
import warnings
import time
import textwrap
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.messages import HumanMessage
from src.graph.workflow import createNetworkAssistantGraph
from src.graph.state import NetworkState, DeviceConnection

# --- CONFIGURATION ---
GNS3_IP = "127.0.0.1"
GNS3_PORT = "3080"
BASE_URL = f"http://{GNS3_IP}:{GNS3_PORT}/v2"
PROJECT_ID = "f900d9db-2b75-4a90-8d6e-59b49f92af35"

os.environ["LANGCHAIN_TRACING"] = "false"
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

graphInstance = None
deviceObjectInstance = None
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

# --- GNS3 HELPER FUNCTIONS ---
def checkGNS3Connectivity() -> bool:
    """Kiểm tra kết nối tới GNS3 Server trước khi khởi động Agent"""
    try:
        response = requests.get(f"{BASE_URL}/version", timeout=5)
        response.raise_for_status()
        version = response.json().get("version")
        logger.info(f"Kết nối GNS3 Server thành công (v{version})")
        
        proj_resp = requests.get(f"{BASE_URL}/projects/{PROJECT_ID}", timeout=5)
        if proj_resp.status_code == 200:
            logger.info(f"Project '{proj_resp.json().get('name')}' sẵn sàng.")
            return True
        else:
            logger.error(f"Không tìm thấy Project ID: {PROJECT_ID}")
            return False
    except Exception as e:
        logger.error(f"Lỗi kết nối GNS3: {e}")
        return False

# --- SYSTEM INITIALIZATION ---

def initializeSystem() -> bool:
    global graphInstance, deviceObjectInstance
    
    print("\n\033[92m[HỆ THỐNG] Bắt đầu khởi tạo ứng dụng...\033[0m")
    
    if not checkGNS3Connectivity():
        return False
    
    device_config = loadDeviceConfig()
    if not device_config:
        logger.error("Không thể load config thiết bị từ devices.yaml")
        return False
    
    deviceObjectInstance = createDeviceConnection(device_config)
    
    try:
        graphInstance = createNetworkAssistantGraph()
        logger.info("Đã khởi tạo LangGraph workflow")
    except Exception as e:
        logger.error(f"Lỗi khởi tạo graph: {e}")
        return False
    
    print("\033[92m[HỆ THỐNG] Khởi tạo hoàn tất!\033[0m\n")
    return True

def loadDeviceConfig():
    try:
        config_path = Path("config/devices.yaml")
        if not config_path.exists(): return None
        with open(config_path, 'r', encoding='utf-8') as f:
            devices = yaml.safe_load(f)
            
        if devices:
            first_device_key = list(devices.keys())[0]
            return devices.get(first_device_key)
        return None
        
    except Exception as e:
        logger.error(f"Lỗi config: {e}")
        return None

def createDeviceConnection(device_config: dict):
    try:
        return DeviceConnection(
            hostname=str(device_config.get("hostname", "")),
            device_type=str(device_config.get("device_type", "cisco_ios")),
            username=str(device_config.get("username", "")),
            password=str(device_config.get("password", "")),
            secret=str(device_config.get("secret")),
            port=int(device_config.get("port", 22))
        )
    except Exception as e:
        logger.error(f"Lỗi tạo DeviceConnection: {e}"); return None

# --- PROCESS & FORMATTING ---

def processQuery(query: str, thread_id: str = "default", is_resume: bool = False):
    global graphInstance, deviceObjectInstance
    if not graphInstance: return
    
    config = {"configurable": {"thread_id": thread_id}}
    print("\n\033[92m[HỆ THỐNG] Đang xử lý yêu cầu...\033[0m")
    
    try:
        # 1. GỌI ĐỒ THỊ (Khởi tạo mới hoặc Tiếp tục từ điểm bị ngắt)
        if is_resume:
            from langgraph.types import Command
            stream_generator = graphInstance.stream(Command(resume=query), config)
        else:
            initial_state = NetworkState(
                messages=[HumanMessage(content=query)],
                target_device=deviceObjectInstance,
                devices=[deviceObjectInstance] if deviceObjectInstance else []
            )
            stream_generator = graphInstance.stream(initial_state, config)

        raw_outputs_to_print = {}

        # 2. VÒNG LẶP XỬ LÝ VÀ IN DỮ LIỆU
        for chunk in stream_generator:
            if "extract_data" in chunk:
                raw_outputs_to_print = chunk["extract_data"].get("command_outputs", {})

            if "analyst" in chunk:
                # --- IN KHUNG DỮ LIỆU RAW (NẾU CÓ) ---
                if raw_outputs_to_print:
                    content_width = 120
                    frame_width = content_width + 4
                    
                    print("\n\t\033[96m" + "╔" + "═"*(frame_width-2) + "╗" + "\033[0m")
                    
                    title = "║ [RAW DATA] KẾT QUẢ THỰC THI TỪ THIẾT BỊ"
                    print("\t\033[96m" + title + " "*(frame_width - len(title) - 1) + "║\033[0m")
                    print("\t\033[96m" + "╠" + "═"*(frame_width-2) + "╣" + "\033[0m")
                    
                    tool_count = len(raw_outputs_to_print)
                    current_tool = 0
                    
                    for tool_name, result in raw_outputs_to_print.items():
                        current_tool += 1
                        display_text = str(result)
                        try:
                            parsed_data = json.loads(display_text)
                            if isinstance(parsed_data, dict):
                                if parsed_data.get("success") is False:
                                    display_text = f"LỖI: {parsed_data.get('error', 'Không rõ nguyên nhân')}"
                                elif "output" in parsed_data:
                                    display_text = str(parsed_data["output"])
                        except Exception:
                            pass 

                        tool_line = f"Tool đã dùng: {tool_name}"
                        print("\t\033[96m║ \033[93m" + tool_line.ljust(content_width) + " \033[96m║\033[0m")
                        print("\t\033[96m║ \033[90m" + "Output:".ljust(content_width) + " \033[96m║\033[0m")
                        
                        for line in display_text.split('\n'):
                            safe_line = line.replace('\r', '')[:content_width] 
                            print("\t\033[96m║ \033[90m" + safe_line.ljust(content_width) + " \033[96m║\033[0m")
                        
                        if current_tool < tool_count:
                            print("\t\033[96m" + "╠" + "═"*(frame_width-2) + "╣" + "\033[0m")

                    print("\t\033[96m" + "╚" + "═"*(frame_width-2) + "╝" + "\033[0m\n")

                # --- IN KHUNG PHÂN TÍCH CỦA ANALYST ---
                msg = chunk["analyst"].get("messages", [])[-1]
                if hasattr(msg, 'content') and msg.content:
                    lines = msg.content.split('\n')
                    wrapped_lines = []
                    content_width = 120 
                    
                    for line in lines:
                        if len(line) > content_width:
                            wrapped_lines.extend(textwrap.wrap(line, width=content_width, replace_whitespace=False))
                        else:
                            wrapped_lines.append(line)
                    
                    frame_width = content_width + 4
                    print("\033[93m\t" + "╔" + "═"*(frame_width-2) + "╗" + "\033[0m")
                    title = "║ [ANALYST] PHẢN HỒI"
                    print("\033[93m\t" + title + " "*(frame_width - len(title) - 1) + "║" + "\033[0m")
                    
                    for line in wrapped_lines:
                        content_line = "║ " + line.ljust(content_width) + " ║"
                        print("\t" + content_line)
                        
                    print("\033[93m\t" + "╚" + "═"*(frame_width-2) + "╝" + "\033[0m")

        # 3. CHỐT CHẶN HITL: Kiểm tra trạng thái Graph sau khi vòng lặp dừng
        state = graphInstance.get_state(config)
        if state.tasks and state.tasks[0].interrupts:
            interrupt_msg = state.tasks[0].interrupts[0].value
            
            print(f"\n\033[91m [CẢNH BÁO BẢO MẬT] AI YÊU CẦU QUYỀN THỰC THI:\033[0m")
            print(f"\033[93m\t{interrupt_msg}\033[0m")
            
            # Hỏi ý kiến user
            user_approval = input("\t\033[92m 👉 Bạn có đồng ý thực thi không? (yes/no): \033[0m").strip()
            
            # Gọi đệ quy hàm processQuery để mở khóa Graph tiếp tục chạy
            processQuery(user_approval, thread_id=thread_id, is_resume=True)
            
    except Exception as e:
        print(f"\n\033[91m[LỖI THỰC THI] {e}\033[0m")

def interactiveMode():
    if not initializeSystem():
        print("\033[91m[LỖI] Khởi tạo thất bại. Vui lòng kiểm tra GNS3 VM và Config.\033[0m")
        return
    
    print("\033[92m╔════════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[92m║                          NETWORK AI ASSISTANT                          ║\033[0m")
    print("\033[92m╠────────────────────────────────────────────────────────────────────────╣\033[0m")
    print("\033[92m║ - GNS3 Server: Connected (172.0.0.1)                                   ║\033[0m")
    print("\033[92m║ - Enter your request (Enter Q to quit)                                 ║\033[0m")
    print("\033[92m╚════════════════════════════════════════════════════════════════════════╝\033[0m")
    
    session_thread_id = f"session_cli_{int(time.time())}"
    query_count = 0
    
    while True:
        try:
            print(f"\n[Phiên làm việc #{query_count + 1}]")
            query = input("\t\033[93m ➤  Yêu cầu của bạn: \033[0m").strip()
            
            if query.lower() in ['q', 'exit']: 
                print("\033[92m[HỆ THỐNG] Đang thoát... Tạm biệt!\033[0m")
                break
            if not query: continue
            
            query_count += 1
            processQuery(query, thread_id=session_thread_id)
            
        except KeyboardInterrupt: 
            print("\n\033[91m[HỆ THỐNG] Đã ngắt bởi người dùng.\033[0m")
            break

if __name__ == "__main__":   
    interactiveMode()