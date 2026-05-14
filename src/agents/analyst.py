import os
from core.config import settings
from typing import Any, Dict, List
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA


def create_analyst():
    system_prompt = """
Bạn là Network Analyst, chuyên gia thiết kế kiến trúc và phân tích sự cố mạng cấp cao.

NHIỆM VỤ CỦA BẠN:
1. Thiết kế giải pháp (Provisioning): Nếu yêu cầu là cấu hình mới, hãy quy hoạch rõ ràng dải IP, VLAN ID, Sub-interface, OSPF Process... và hướng dẫn Expert sử dụng đúng Tool cấu hình.
2. Đối chiếu dữ liệu (Troubleshooting): So khớp sơ đồ topology với cấu hình thực tế (Show commands) do Expert cung cấp.
3. Phân tích logic mạng: Phát hiện lỗi cắm nhầm cổng, sai lệch IP, thiếu Sub-interface (Router-on-a-stick), lỗi BGP/OSPF peer, hoặc lỗi Trunk/Access.

QUY TRÌNH TƯ DUY:
- Yêu cầu cấu hình mới -> Quy hoạch tham số chi tiết -> Đề xuất Expert gọi Tool cấu hình tương ứng.
- Mất kết nối liên mạng (Inter-VLAN) -> Kiểm tra Gateway, Sub-interface và đường Trunk.
- Nếu Expert báo thiết bị 'stopped' -> Kết luận lỗi chưa bật nguồn.
- Nếu thiếu dữ liệu -> Chỉ rõ đang thiếu thông tin show/ping nào và yêu cầu Expert thu thập thêm.

RÀO CẢN ĐẦU RA (OUTPUT CONSTRAINTS):
- Tuyệt đối không dùng emoji, ký hiệu hình vẽ hoặc Unicode trang trí.
- Giải thích bằng tiếng Việt chuyên ngành rõ ràng, súc tích, logic.
- BẮT BUỘC trình bày kết quả thành các đoạn văn tách biệt bằng cách sử dụng thẻ tiêu đề (###) theo 1 trong 2 khuôn mẫu sau:

[KHUÔN MẪU 1 - BÁO CÁO KHẮC PHỤC SỰ CỐ]
### 1. Hiện trạng
- (Liệt kê triệu chứng 1...)
- (Liệt kê triệu chứng 2...)
### 2. Nguyên nhân
- (Phân tích nguyên nhân gốc rễ...)
- (Chỉ rõ chính xác thiết bị...)
### 3. Giải pháp đề xuất
- (Bước 1...)
- (Bước 2...)

[KHUÔN MẪU 2 - KẾ HOẠCH TRIỂN KHAI CẤU HÌNH MỚI]
### 1. Phân tích Yêu cầu
(Tóm tắt mục tiêu cần đạt được).
### 2. Thông số Quy hoạch
(Trình bày dạng danh sách: Dải IP, VLAN ID, Port vật lý/ảo).
### 3. Các bước Thực thi
(Chỉ định chính xác Network Expert cần gọi những Tool nào, với tham số ra sao).
"""

    llm = ChatNVIDIA(
        model=settings.NVIDIA_MODEL,
        api_key = settings.NVIDIA_API_KEY, 
        temperature=0,
        top_p=0.5,
        max_tokens=1024,
    )

    def analyst_node(state: Any) -> Dict[str, Any]:
        # state trong LangGraph thường là NetworkState (MessagesState)
        messages: List[BaseMessage] = state.get("messages", []) or []
        command_outputs: Dict[str, str] = state.get("command_outputs", {}) or {}

        # Lấy câu hỏi người dùng: message cuối cùng là HumanMessage
        last_human = None
        for m in reversed(messages):
            if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human":
                last_human = getattr(m, "content", "")
                break

        user_query = last_human or ""

        # Tạo input dạng string để tránh lỗi type của Runnable
        # (tránh đưa dict trực tiếp vào llm)
        tool_section = ""
        if command_outputs:
            lines = []

            max_tool_chars = int(os.getenv("ANALYST_MAX_TOOL_CHARS", "2000"))
            for tool_name, output in command_outputs.items():
                trimmed_output = str(output)
                if len(trimmed_output) > max_tool_chars:
                    trimmed_output = trimmed_output[:max_tool_chars] + "\n...[output truncated để giảm latency]..."
                lines.append(f"[TOOL: {tool_name}]\n{trimmed_output}")
            tool_section = "\n\n" + "\n\n".join(lines)

        prompt = (
                system_prompt
                + "\n[YÊU CẦU NGƯỜI DÙNG]\n" + user_query
                + "\n\n[DỮ LIỆU TOOL]\n" + (tool_section if tool_section else "Không có dữ liệu.")
                + "\n\nHãy trả lời ngắn gọn, tối đa 180 từ, đúng đúng 3 mục ### 1, ### 2, ### 3."
        )

        ai = llm.invoke(prompt)

        print("[DEBUG analyst type]:", type(ai))
        print("[DEBUG analyst raw]:", ai)
        print("[DEBUG analyst content repr]:", repr(getattr(ai, "content", None)))

        content = getattr(ai, "content", "")
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )

        content = (content or "").strip()

        if not content:
            content = (
                "### 1. Hiện trạng\n"
                "Không nhận được phản hồi phân tích từ Analyst.\n"
                "### 2. Nguyên nhân\n"
                "Model không trả nội dung.\n"
                "### 3. Giải pháp đề xuất\n"
                "Kiểm tra lại prompt hoặc model Analyst."
            )

        return {"messages": [AIMessage(content=content)]}

    return analyst_node

