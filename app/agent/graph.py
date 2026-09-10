from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.agent.state import TravelState
from app.agent.nodes import (
    route_intent,
    route_after_intent,
    flight_agent,
    hotel_agent,
    itinerary_agent,
    final_agent,
    followup_agent,
)
from app.agent.pdf_export import pdf_agent
from app.config import DATABASE_URL, DB_POOL_MAX_SIZE
from app.logging_config import logger

# A pooled connection (NOT a single shared connection) is required once you
# have concurrent requests, since psycopg connections are not thread-safe.
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=DB_POOL_MAX_SIZE,
    kwargs={"autocommit": True, "row_factory": dict_row},
)

checkpointer = PostgresSaver(pool)
checkpointer.setup()

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

travel_graph = builder.compile(checkpointer=checkpointer)

logger.info("Travel graph compiled and checkpointer initialized.")

''''''

def check_db_health() -> bool:
    """Used by the /health endpoint's liveness probe."""
    try:
        with pool.connection(timeout=3) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
