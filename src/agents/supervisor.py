from typing import Literal

from langgraph.graph import END
from langgraph.types import Command

from src.graph.state import NetworkState


class SupervisorAgent:
    def route(self, state: NetworkState):
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        # Nếu tin cuối cùng là yêu cầu người dùng => chuyển sang Network Expert
        if last_message and last_message.type == "human":
            print("\033[95m[SUPERVISOR] Nhận yêu cầu mới. Chuyển sang ➔ NETWORK EXPERT ...\033[0m")
            return Command(
                goto="network_expert",
                update={
                    "current_phase": "collecting",
                    "command_outputs": {},
                },
            )

        # Nếu đã phân tích xong => kết thúc
        if state.get("current_phase") == "analyzed":
            print("\033[95m[SUPERVISOR] Phân tích hoàn tất. Kết thúc workflow.\033[0m")
            return Command(goto=END, update={"current_phase": "finished"})

        # Xác định đã có output tool trong messages chưa
        has_tool_output = any(getattr(msg, "type", None) == "tool" for msg in messages)
        has_collected_data = bool(state.get("command_outputs"))

        # Nếu chưa có tool output => phải chạy network_expert để hoàn tất tool_calls
        # (tránh nhảy sang analyst/END khi đang ở giữa vòng gọi tool)
        if not has_tool_output:
            print("\033[95m[SUPERVISOR] Chưa có tool output trong chat history. Giữ ở NETWORK EXPERT ...\033[0m")
            return Command(
                goto="network_expert",
                update={"current_phase": "collecting"},
            )

        # Có tool output => nếu chưa analyzed thì chuyển analyst
        if state.get("current_phase") != "analyzed":
            print(
                "\033[95m[SUPERVISOR] Có tool/output (tool_messages=%s, command_outputs=%s). Chuyển ➔ ANALYST ...\033[0m"
                % (int(has_tool_output), int(has_collected_data))
            )
            return Command(
                goto="analyst",
                update={"current_phase": "analyzing"},
            )

        return Command(goto=END)

