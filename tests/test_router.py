"""
Run with: pytest tests/test_router.py
Mocks the LLM so this doesn't hit Groq or need real env vars beyond
the minimal ones config.py requires at import time.
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure required env vars exist before app.config is imported
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.nodes import route_intent, route_after_intent  # noqa: E402


def _fake_response(text):
    resp = MagicMock()
    resp.content = text
    return resp


def test_no_existing_itinerary_is_always_new_trip():
    state = {"user_query": "plan me a trip to Japan", "itinerary": ""}
    result = route_intent(state)
    assert result["intent"] == "new_trip"


@patch("app.agent.nodes.llm")
def test_followup_classified_correctly(mock_llm):
    mock_llm.invoke.return_value = _fake_response("followup")
    state = {"user_query": "can you make the hotel cheaper?", "itinerary": "Day 1: ..."}
    result = route_intent(state)
    assert result["intent"] == "followup"


@patch("app.agent.nodes.llm")
def test_new_destination_classified_as_new_trip(mock_llm):
    mock_llm.invoke.return_value = _fake_response("new_trip")
    state = {"user_query": "actually let's plan a trip to Peru instead", "itinerary": "Day 1: ..."}
    result = route_intent(state)
    assert result["intent"] == "new_trip"


def test_route_after_intent_fans_out_for_new_trip():
    assert route_after_intent({"intent": "new_trip"}) == ["flight_agent", "hotel_agent"]


def test_route_after_intent_goes_to_followup_agent():
    assert route_after_intent({"intent": "followup"}) == ["followup_agent"]
