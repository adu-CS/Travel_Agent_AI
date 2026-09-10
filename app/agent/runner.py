import uuid

from langchain_core.messages import HumanMessage

from app.agent.graph import travel_graph
from app.logging_config import logger


def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    is_new_thread = thread_id is None
    if is_new_thread:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}

    # Only seed empty defaults on a brand-new thread. On subsequent calls
    # with the same thread_id, omit these keys entirely so PostgresSaver
    # restores the last checkpointed values instead of wiping them.
    input_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
    }
    if is_new_thread:
        input_state.update({
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "intent": "",
            "pdf_path": "",
            "llm_calls": 0,
        })

    logger.info(f"run_travel_agent thread_id={thread_id} new_thread={is_new_thread}")

    result = travel_graph.invoke(input_state, config=config)
    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "intent": result.get("intent", ""),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "pdf_path": result.get("pdf_path", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
