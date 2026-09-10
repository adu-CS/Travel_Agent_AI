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
