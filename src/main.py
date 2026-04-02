import os
import yaml
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.messages import HumanMessage
from src.graph.workflow import create_network_assistant_graph
from src.graph.state import NetworkState, DeviceConnection
import logging
import time

# Disable LangSmith & Load environment variables
os.environ["LANGCHAIN_TRACING"] = "false"
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_device_config(device_name: str = None):
    """Load device configuration từ file YAML"""
    try:
        config_path = Path("config/devices.yaml")
        if not config_path.exists():
            logger.warning("Không tìm thấy file config/devices.yaml")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            devices = yaml.safe_load(f)
            
        if device_name and device_name in devices:
            return devices[device_name]
        elif "default" in devices:
            return devices["default"]
        else:
            return None
            
    except Exception as e:
        logger.error(f"Lỗi đọc file config/devices.yaml: " + str(e))
        return None

def create_device_connection(device_config: dict):
    """Tạo DeviceConnection object từ config dict"""
    if not device_config:
        return None
        
    try:
        device_obj = DeviceConnection(
            hostname=str(device_config.get("hostname", "")),
            device_type=str(device_config.get("device_type", "cisco_ios")),
            username=str(device_config.get("username", "")),
            password=str(device_config.get("password", "")),
            secret=str(device_config.get("secret")),
            port=int(device_config.get("port", 22))
        )
        logger.info(f"✅ Đã tạo kết nối đến thiết bị: {device_obj.hostname}")
        return device_obj
        
    except Exception as e:
        logger.error(f"❌ Lỗi tạo DeviceConnection: {e}")
        return None

def test_ssh_connection(device_config: dict) -> bool:
    """Kiểm tra kết nối SSH trước khi chạy"""
    try:
        from netmiko import ConnectHandler
        
        device = {
            'device_type': device_config.get('device_type', 'cisco_ios'),
            'host': device_config.get('hostname'),
            'username': device_config.get('username'),
            'password': device_config.get('password'),
            'secret': device_config.get('secret'),
            'port': device_config.get('port', 22),
            'conn_timeout': 10,
        }
        
        connection = ConnectHandler(**device)
        connection.disconnect()
        logger.info("✅ SSH connection test successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ SSH connection test failed: {e}")
        return False

def process_query(query: str, device_name: str = None, thread_id: str = "default"):
    """Xử lý câu hỏi của người dùng"""
    start_time = time.time()
    logger.info(f"🚀 Bắt đầu xử lý câu hỏi: {query[:255]}...")
    
    try:
        # Load device config
        device_config = load_device_config(device_name)
        if not device_config:
            logger.error("Không có cấu hình thiết bị")
            print("❌ Không tìm thấy cấu hình thiết bị. Vui lòng kiểm tra config/devices.yaml")
            return None
        
        # Test SSH connection
        if not test_ssh_connection(device_config):
            print("❌ Không thể kết nối SSH đến thiết bị. Vui lòng kiểm tra mạng và thông tin đăng nhập.")
            return None
        
        # Load graph
        logger.info("🔄 Đang khởi tạo graph...")
        graph = create_network_assistant_graph()
        
        # Create device connection object
        device_obj = create_device_connection(device_config)
        
        # Create initial state
        logger.info("📝 Đang tạo initial state...")
        initial_state = NetworkState(
            messages=[HumanMessage(content=query)],
            target_device=device_obj,
            devices=[device_obj] if device_obj else []
        )
        
        # Configure thread
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Run graph
        logger.info("⚙️ Đang chạy LangGraph workflow...")
        invoke_start = time.time()
        # final_state = graph.invoke(initial_state, config)
        print("\n🔄 Đang xử lý...\n")
        for chunk in graph.stream(initial_state, config):
            print(chunk, end="", flush=True)
        final_state = None  # Streaming không trả về final state trực tiếp
        invoke_time = time.time() - invoke_start
        
        logger.info(f"✅ Workflow hoàn thành trong {invoke_time:.2f}s")
        
        # Log results
        if final_state.get("final_report"):
            logger.info("📄 Đã tạo báo cáo")
            print("\n" + "="*80)
            print(final_state["final_report"])
            print("="*80 + "\n")
        else:
            logger.warning("⚠️ Không có báo cáo")
            print(f"\n📊 Trạng thái: {final_state.get('current_phase', 'N/A')}")
            if final_state.get("analysis_results"):
                print(f"📈 Kết quả phân tích: {final_state.get('analysis_results')}")
        
        total_time = time.time() - start_time
        logger.info(f"🏁 Tổng thời gian xử lý: {total_time:.2f}s")
        
        return final_state
        
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý: {e}", exc_info=True)
        print(f"❌ Đã xảy ra lỗi: {e}")
        return None

def interactive_mode():
    """Chạy interactive mode"""
    print("||" + "="*100 + "||")
    print("||🤖 NETWORK AI ASSISTANT - HỖ TRỢ XỬ LÝ SỰ CỐ MẠNG           " + " "*40 + "||")
    print("||" + "-"*100 + "||")
    print("|| - Nhập câu hỏi của bạn (tiếng Việt), hoặc 'Q' để thoát     " + " "*40 + "||")
    print("|| - Ví dụ: 'Hãy kiểm tra tại sao VLAN 10 mất kết nối'        " + " "*40 + "||")
    print("||" + "="*100 + "||")
    
    thread_id = f"session_{os.getpid()}"
    
    while True:
        try:
            query = input("\n- Your question (press 'Q' to quit): ").strip()
            
            if query.lower() in ['q', 'Q']:
                print("\n\n👋 Tạm biệt!")
                break
            
            if not query:
                continue
            
            device = input("- Thiết bị (Enter để dùng mặc định): ").strip()
            
            process_query(query, device if device else None, thread_id)
            
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            break
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}", exc_info=True)
            print(f"❌ Đã xảy ra lỗi: {str(e)}")

if __name__ == "__main__":
    # Kiểm tra file config
    config_path = Path("config/devices.yaml")
    if not config_path.exists():
        print("⚠️ Không tìm thấy file config/devices.yaml")
        print("📝 Tạo file config mặc định...")
        config_path.parent.mkdir(exist_ok=True)
        default_config = {
            "default": {
                "hostname": "192.168.116.167",
                "device_type": "cisco_ios",
                "username": "admin",
                "password": "123456",
                "secret": "123456",
                "port": 22
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        print("✅ Đã tạo file config mặc định")
    
    interactive_mode()


# import logging
# import os
# import yaml
# from dotenv import load_dotenv
# from pathlib import Path
# from langchain_core.messages import HumanMessage
# from src.graph.workflow import create_network_assistant_graph
# from src.utils.logger import setup_logger
# from src.utils.config import load_device_config

# # Load environment variables
# load_dotenv()

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s | %(levelname)-8s | %(message)s',
#     datefmt='%H:%M:%S'
# )
# logger = logging.getLogger(__name__)

# def process_query(query: str, device_name: str = None, thread_id: str = "default"):
#     """
#     Xử lý câu hỏi của người dùng
    
#     Args:
#         query: Câu hỏi bằng tiếng Việt
#         device_name: Tên thiết bị trong config (optional)
#         thread_id: ID của conversation thread
        
#     Returns:
#         Kết quả xử lý
#     """
#     # Load graph
#     graph = create_network_assistant_graph()
    
#     # Load device config nếu có
#     devices = load_device_config()
#     target_device = devices.get(device_name) if device_name else devices.get("default")
    
#     # Tạo initial state
#     initial_state = {
#         "messages": [HumanMessage(content=query)],
#         "target_device": target_device,
#         "current_phase": "start"
#     }
    
#     # Cấu hình thread
#     config = {
#         "configurable": {
#             "thread_id": thread_id
#         }
#     }
    
#     # Chạy graph
#     logger.info(f"Processing query: {query}")
#     final_state = graph.invoke(initial_state, config)
    
#     # Log kết quả
#     if final_state.get("final_report"):
#         logger.info("Report generated successfully")
#         print("\n" + "="*80)
#         print(final_state["final_report"])
#         print("="*80 + "\n")
#     else:
#         logger.warning("No final report generated")
    
#     return final_state

# def interactive_mode():
#     """Chạy interactive mode"""
#     print("||" + "="*100 + "||")
#     print("||🤖 NETWORK AI ASSISTANT - HỖ TRỢ XỬ LÝ SỰ CỐ MẠNG           " + " "*40 + "||")
#     print("||" + "-"*100 + "||")
#     print("|| - Nhập câu hỏi của bạn (tiếng Việt), hoặc 'Q' để thoát     " + " "*40 + "||")
#     print("|| - Ví dụ: 'Hãy kiểm tra tại sao VLAN 10 mất kết nối'        " + " "*40 + "||")
#     print("||" + "="*100 + "||")
    
#     thread_id = f"session_{os.getpid()}"
    
#     while True:
#         try:
#             query = input("\n- Your question (press 'Q' to quit): ").strip()
            
#             if query.lower() in ['q', 'Q']:
#                 print("\n\n👋 Tạm biệt giáo chủ!")
#                 break
            
#             if not query:
#                 continue
            
#             # Hỏi tên thiết bị
#             device = input("- Thiết bị (Enter để dùng mặc định): ").strip()
            
#             # Xử lý
#             result = process_query(query, device if device else None, thread_id)
            
#             # Hỏi feedback
#             feedback = input("\n📝 Bạn có hài lòng với kết quả? (y/n): ").strip()
#             if feedback.lower() == 'n':
#                 print("Cảm ơn phản hồi của bạn. Chúng tôi sẽ cải thiện!")
            
#         except KeyboardInterrupt:
#             print("\n\n👋 Tạm biệt giáo chủ!")
#             break
#         except Exception as e:
#             logger.error(f"Lỗi: {str(e)}")
#             print(f"❌ Đã xảy ra lỗi: {str(e)}")

# if __name__ == "__main__":
#     interactive_mode()