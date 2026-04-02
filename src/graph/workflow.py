from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import NetworkState
from src.agents.supervisor import SupervisorAgent
from src.agents.network_expert import create_network_expert
from src.agents.analyst import create_analyst

def create_network_assistant_graph():
    supervisor = SupervisorAgent()
    network_expert = create_network_expert()
    analyst = create_analyst()

    builder = StateGraph(NetworkState)

    builder.add_node("supervisor", supervisor.route)
    builder.add_node("network_expert", network_expert)
    builder.add_node("analyst", analyst)

    builder.add_edge(START, "supervisor")

    # Conditional edges từ supervisor
    builder.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_agent", "__end__"),
        {
            "network_expert": "network_expert",
            "analyst": "analyst",
            "__end__": END
        }
    )

    # Sau khi network_expert chạy xong, quay về supervisor
    builder.add_edge("network_expert", "supervisor")
    
    # Sau khi analyst chạy xong, cập nhật state và quay về supervisor
    def after_analyst(state: NetworkState):
        # Đánh dấu đã có kết quả phân tích
        return {"analysis_results": {"status": "completed"}, "current_phase": "analyzed"}
    
    builder.add_node("after_analyst", after_analyst)
    builder.add_edge("analyst", "after_analyst")
    builder.add_edge("after_analyst", "supervisor")

    graph = builder.compile(checkpointer=MemorySaver())

    return graph