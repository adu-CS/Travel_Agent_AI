from langgraph.graph import StateGraph, START, END
import operator
from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    intent: str
    pdf_path: str
    # operator.add lets parallel nodes (flight_agent + hotel_agent) safely
    # increment this counter without clobbering each other's writes.
    llm_calls: Annotated[int, operator.add]

builder = StateGraph(TravelState)

builder.add_node("route_intent", route_intent)
builder.add_node("flight_agent", flight_agent)
builder.add_node("hotel_agent", hotel_agent)
builder.add_node("itinerary_agent", itinerary_agent)
builder.add_node("final_agent", final_agent)
builder.add_node("followup_agent", followup_agent)
builder.add_node("pdf_agent", pdf_agent)

builder.add_edge(START, "route_intent")
builder.add_conditional_edges("route_intent", route_after_intent)

builder.add_edge(["flight_agent", "hotel_agent"], "itinerary_agent")
builder.add_edge("itinerary_agent", "final_agent")

builder.add_edge("final_agent", "pdf_agent")
builder.add_edge("followup_agent", "pdf_agent")
builder.add_edge("pdf_agent", END)