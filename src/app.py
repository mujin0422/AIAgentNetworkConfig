import customtkinter as ctk
import threading
import time
import markdown
from tkhtmlview import HTMLLabel
from PIL import Image
from langchain_core.messages import HumanMessage
from src.graph.state import NetworkState
from src.graph.workflow import createNetworkAssistantGraph
from src.main import checkGNS3Connectivity, loadDeviceConfig, createDeviceConnection

# --- CẤU HÌNH GIAO DIỆN ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class NetworkAssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Network AI Assistant")
        self.geometry("650x800")
        self.configure(fg_color="#0F0F0F") 
        self.graph = None
        self.device_obj = None
        self.thread_id = f"session_{int(time.time())}"
        self.loading_container = None
        self.setupUi()
        self.initBackend()

    # --- GIAO DIỆN & XỬ LÝ HIỂN THỊ ---
    def setupUi(self):
        # 1. Khung cuộn hiển thị lịch sử chat
        self.chat_display = ctk.CTkScrollableFrame(
            self, 
            fg_color="#0F0F0F", # Nền đen
            scrollbar_button_color="#4a4a4a"
        )
        self.chat_display.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        # 2. Khung chứa ô nhập liệu dưới cùng
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(padx=20, pady=(0, 20), fill="x", side="bottom")

        # 2.1. Ô nhập liệu bo góc mềm mại
        self.entry = ctk.CTkEntry(
            self.input_frame, 
            placeholder_text="Nhập yêu cầu kiểm tra hệ thống mạng...", 
            font=("Roboto", 15),
            height=40,
            corner_radius=20,
            border_width=1,
            border_color="#333333",
            fg_color="#1E1E1E", 
            text_color="#FFFFFF"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda event: self.sendMessage())

        # 2.2. Nút gửi với icon
        try:
            icon_image = ctk.CTkImage(
                light_image=Image.open("images/icon/send.png"),
                dark_image=Image.open("images/icon/send.png"),
                size=(22, 22)
            )
        except Exception as e:
            print(f"Không thể tải ảnh icon: {e}")
            icon_image = None 

        self.send_btn = ctk.CTkButton(
            self.input_frame, 
            text="", 
            image=icon_image, 
            command=self.sendMessage, 
            width=40, 
            height=40,
            fg_color="#0F0F0F", 
            hover_color="#1E1E1E"
        )
        self.send_btn.pack(side="right")

    # --- KẾT NỐI BACKEND & XỬ LÝ LOGIC ---
    def addMessage(self, sender, text):
        """Hàm vẽ từng bong bóng chat dựa vào người gửi"""
        container = ctk.CTkFrame(self.chat_display, fg_color="transparent")
        container.pack(fill="x", pady=10, padx=5)

        if sender == "user":
            # Tin nhắn User
            bubble = ctk.CTkFrame(container, fg_color="#2B2B2B", corner_radius=20)
            bubble.pack(side="right", padx=(50, 5))
            lbl = ctk.CTkLabel(bubble, text=text, font=("Roboto", 15), text_color="#FFFFFF", wraplength=450, justify="left")
            lbl.pack(padx=20, pady=10)

        elif sender == "ai":
            # Tin nhắn AI
            avatar = ctk.CTkLabel(container, text="✨", font=("Roboto", 22), text_color="#1a73e8")
            avatar.pack(side="left", anchor="nw", padx=(5, 10), pady=5)
            
            bubble = ctk.CTkFrame(container, fg_color="#1E1E1E", corner_radius=20)
            bubble.pack(side="left", fill="both", expand=True, padx=(0, 50))
            
           # 1. Chuyển đổi Markdown của AI sang HTML
            html_content = markdown.markdown(text)
            
            # 2. XÓA BỎ MỌI DẤU XUỐNG DÒNG NGẦM (Lỗi lớn nhất khiến tkhtmlview sinh margin ảo)
            html_content = html_content.replace('\n', '')
            
            # 3. PHÁ BỎ CÁC THẺ GÂY MARGIN, TỰ ĐIỀU KHIỂN XUỐNG DÒNG BẰNG <br>
            html_content = html_content.replace('<h3>', '<b style="color: #FFFFFF; font-family: Roboto; font-size:12px;">')
            html_content = html_content.replace('</h3>', '</b><br>')
            html_content = html_content.replace('<ul>', '')
            html_content = html_content.replace('</ul>', '<br>')
            html_content = html_content.replace('<li>', '<span style="color: #FFFFFF; font-family: Roboto; font-size: 12px;"> - ')
            html_content = html_content.replace('</li>', '</span><br>')
            html_content = html_content.replace('<p>', '<span style="color: #FFFFFF; font-family: Roboto; font-size: 12px;">')
            html_content = html_content.replace('</p>', '</span><br>')
            
            if html_content.endswith('<br>'):
                html_content = html_content[:-4]

            # 4. Dùng HTMLLabel để hiển thị & Tự động co giãn chiều cao
            box = HTMLLabel(
                bubble, 
                html=html_content, 
                background="#1E1E1E", 
                borderwidth=0, 
                highlightthickness=0
            )
            box.pack(fill="both", expand=True, padx=15, pady=10)
            box.fit_height()

        elif sender == "system":
            lbl = ctk.CTkLabel(container, text=text, font=("Roboto", 15, "italic"), text_color="#888888")
            lbl.pack(anchor="center")

        # Cập nhật và cuộn xuống dưới cùng
        self.update_idletasks()
        self.chat_display._parent_canvas.yview_moveto(1.0)

    # Hàm hiển thị trạng thái đang xử lý và ẩn đi sau khi có kết quả
    def showLoading(self):
        self.loading_container = ctk.CTkFrame(self.chat_display, fg_color="transparent")
        self.loading_container.pack(fill="x", pady=10, padx=5)
        
        avatar = ctk.CTkLabel(self.loading_container, text="✨", font=("Roboto", 22), text_color="#1a73e8")
        avatar.pack(side="left", anchor="nw", padx=(5, 10))
        
        lbl = ctk.CTkLabel(self.loading_container, text="Đang quét sơ đồ và phân tích...", font=("Roboto", 15, "italic"), text_color="#888888")
        lbl.pack(side="left", anchor="w")
        
        self.update_idletasks()
        self.chat_display._parent_canvas.yview_moveto(1.0)

    # Ẩn trạng thái đang xử lý khi đã có kết quả từ AI
    def hideLoading(self):
        if self.loading_container:
            self.loading_container.destroy()
            self.loading_container = None

    # Khởi tạo backend trong thread riêng để không block UI
    def initBackend(self):
        self.is_waiting_approval = False # Thêm cờ trạng thái duyệt
        self.addMessage("system", "Đang khởi tạo kết nối GNS3 và nạp Agent...") 
        threading.Thread(target=self.initTask, daemon=True).start() # Khởi tạo backend trong thread riêng để không block UI

    # Hàm khởi tạo backend, kiểm tra kết nối GNS3, nạp cấu hình thiết bị và tạo graph
    def initTask(self):
        if checkGNS3Connectivity():
            config = loadDeviceConfig()
            if config:
                self.device_obj = createDeviceConnection(config)
                self.graph = createNetworkAssistantGraph()
                self.after(0, lambda: self.addMessage("system", "Khởi tạo thành công! Sẵn sàng hỗ trợ bạn."))
            else:
                self.after(0, lambda: self.addMessage("system", "Lỗi: Không thể tải cấu hình thiết bị từ devices.yaml."))
        else:
            self.after(0, lambda: self.addMessage("system", "Lỗi: Không thể kết nối tới GNS3 Server!"))

    # Hàm xử lý khi người dùng gửi tin nhắn, phân biệt giữa câu hỏi mới và trả lời phê duyệt, gọi graph và cập nhật giao diện
    def sendMessage(self):
        user_text = self.entry.get().strip()
        if not user_text or not self.graph:
            return

        self.entry.delete(0, "end")
        self.send_btn.configure(state="disabled")
        
        self.addMessage("user", user_text)
        self.showLoading()

        # Kiểm tra xem đây là câu hỏi mới hay là câu trả lời Yes/No cho lệnh phê duyệt
        is_resume = self.is_waiting_approval
        if is_resume:
            self.is_waiting_approval = False # Đặt lại cờ sau khi đã trả lời

        threading.Thread(target=self.processAi, args=(user_text, is_resume), daemon=True).start()

    # Hàm hiển thị thông báo yêu cầu phê duyệt từ AI (HITL)
    def askUserApproval(self, interrupt_msg):
        self.hideLoading()
        self.is_waiting_approval = True
        # Định dạng nội dung cảnh báo bằng Markdown
        approval_text = f"**YÊU CẦU PHÊ DUYỆT TỪ HỆ THỐNG:**\n\n{interrupt_msg}\n\n *Vui lòng gõ **'yes'** (hoặc y, ok) vào ô chat để đồng ý thực thi, hoặc gõ **'no'** để hủy bỏ.*"
        # In thông báo ra màn hình chat
        self.addMessage("ai", approval_text)
        self.send_btn.configure(state="normal")

    # Hàm xử lý phản hồi từ AI, cập nhật log và hiển thị kết quả cuối cùng, phân biệt giữa dữ liệu thô và phân tích của Analyst
    def processAi(self, user_text, is_resume=False):
        config = {"configurable": {"thread_id": self.thread_id}}
        try:
            # Sử dụng stream_mode="updates" để nhận phản hồi ngay sau mỗi Node
            if is_resume:
                from langgraph.types import Command
                stream_generator = self.graph.stream(Command(resume=user_text), config, stream_mode="updates")
            else:
                initial_state = NetworkState(
                    messages=[HumanMessage(content=user_text)],
                    target_device=self.device_obj,
                    devices=[self.device_obj]
                )
                stream_generator = self.graph.stream(initial_state, config, stream_mode="updates")

            for chunk in stream_generator:
                # --- IN TERMINAL NGAY KHI NETWORK EXPERT CHẠY XONG TOOL ---
                if "network_expert" in chunk:
                    # Lấy các tin nhắn mới nhất từ Expert
                    node_output = chunk["network_expert"]
                    messages = node_output.get("messages", [])
                    
                    # Lọc ra các ToolMessages (kết quả trả về từ thiết bị)
                    tool_messages = [m for m in messages if m.type == "tool"]
                    
                    if tool_messages:
                        self.printRawData(tool_messages)

                if "analyst" in chunk:
                    msg = chunk["analyst"].get("messages", [])[-1]
                    if hasattr(msg, 'content') and msg.content:
                        final_response = msg.content

            # 3. CHỐT CHẶN HITL: Kiểm tra trạng thái Graph sau khi kết thúc vòng lặp
            state = self.graph.get_state(config)
            if state.tasks and state.tasks[0].interrupts:
                interrupt_msg = state.tasks[0].interrupts[0].value
                # Gọi hàm UI hỏi ý kiến người dùng và DỪNG tiến trình xử lý tại đây
                self.after(0, self.askUserApproval, interrupt_msg)
                return 

            # 4. Nếu không bị đóng băng -> Hoàn tất báo cáo và in ra GUI
            self.after(0, self.updateAiRespone,final_response)

        except Exception as e:
            self.after(0, self.updateAiRespone, f"Lỗi hệ thống: {str(e)}")

    def printRawData(self, tool_messages):
        import json
        content_width = 120
        frame_width = content_width + 4
        
        print("\n\t\033[96m" + "╔" + "═"*(frame_width-2) + "╗" + "\033[0m")
        title = "║ [RAW DATA] KẾT QUẢ THỰC THI TỪ THIẾT BỊ"
        print("\t\033[96m" + title + " "*(frame_width - len(title) - 1) + "║\033[0m")
        
        for i, msg in enumerate(tool_messages):
            print("\t\033[96m" + "╠" + "═"*(frame_width-2) + "╣" + "\033[0m")
            
            tool_name = getattr(msg, 'name', 'Unknown Tool')
            display_text = str(msg.content)
            
            try:
                parsed_data = json.loads(display_text)
                if isinstance(parsed_data, dict) and "output" in parsed_data:
                    display_text = str(parsed_data["output"])
            except:
                pass

            print("\t\033[96m║ \033[93m" + f"Tool: {tool_name}".ljust(content_width) + " \033[96m║\033[0m")
            print("\t\033[96m║ \033[90m" + "Output:".ljust(content_width) + " \033[96m║\033[0m")
            
            for line in display_text.split('\n'):
                safe_line = line.replace('\r', '')[:content_width] 
                print("\t\033[96m║ \033[90m" + safe_line.ljust(content_width) + " \033[96m║\033[0m")
        print("\t\033[96m" + "╚" + "═"*(frame_width-2) + "╝" + "\033[0m\n")
        
    # Hàm cập nhật phản hồi của AI lên giao diện, ẩn trạng thái loading và kích hoạt lại nút gửi
    def updateAiRespone(self,final_response):
        self.hideLoading()
        self.addMessage("ai",final_response)
        self.send_btn.configure(state="normal")

if __name__ == "__main__":
    app = NetworkAssistantApp()
    app.mainloop()