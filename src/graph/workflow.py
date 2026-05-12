from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import NetworkState
from src.agents.supervisor import SupervisorAgent
from src.agents.network_expert import create_network_expert
from src.agents.analyst import create_analyst

def extractNetworkData(state: NetworkState):
    """ Node trung gian: Trích xuất nội dung từ ToolMessages vào trường command_outputs. """
    messages = state.get("messages", [])
    new_outputs = {} 
    
    # Duyệt ngược để xác định phạm vi tin nhắn từ sau câu hỏi cuối cùng của Human
    relevant_messages = []
    for msg in reversed(messages):
        if msg.type == "human":
            break
        relevant_messages.append(msg)
            
    # Duyệt xuôi các tin nhắn liên quan để giữ đúng thứ tự thời gian thực thi tool
    for msg in reversed(relevant_messages):
        if msg.type == "tool":
            tool_name = getattr(msg, 'name', 'unknown_tool')
            
            if tool_name not in new_outputs:
                new_outputs[tool_name] = []
            new_outputs[tool_name].append(msg.content)
            
    return {
        "command_outputs": new_outputs,
        "current_phase": "collected" if new_outputs else "start"
    }

def afterAnalyst(state: NetworkState):
    """ Node xử lý sau khi Analyst phản hồi: Lưu nội dung phân tích vào final_report để main.py có thể hiển thị. """
    messages = state.get("messages", [])
    last_content = messages[-1].content if messages else ""
    
    return {
        "analysis_results": {"status": "completed"}, 
        "current_phase": "analyzed",
        "final_report": last_content
    }

def createNetworkAssistantGraph():
    # Khởi tạo các thành phần
    supervisor = SupervisorAgent()
    network_expert = create_network_expert()
    analyst = create_analyst()

    # Khởi tạo đồ thị với NetworkState
    builder = StateGraph(NetworkState)

    #  Định nghĩa các Node
    builder.add_node("supervisor", supervisor.route)
    builder.add_node("network_expert", network_expert)
    builder.add_node("extract_data", extractNetworkData)
    builder.add_node("analyst", analyst)
    builder.add_node("after_analyst", afterAnalyst)

    # Thiết lập luồng chạy (Edges)
    builder.add_edge(START, "supervisor")
    builder.add_edge("network_expert", "extract_data")
    builder.add_edge("extract_data", "supervisor")
    builder.add_edge("analyst", "after_analyst")
    builder.add_edge("after_analyst", "supervisor")

    # Biên dịch đồ thị với bộ nhớ checkpoint
    graph = builder.compile(checkpointer=MemorySaver())

    return graph