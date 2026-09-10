from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY

# Used for tool-calling agents (flight/hotel research, follow-ups).
# A little temperature helps it vary search query phrasing sensibly.
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY,
    temperature=0.2,
)

# Used for itinerary/budget synthesis, where we want minimal creative
# drift on dates and cost figures. Kept as a separate instance so the
# two use cases can be tuned independently.
llm_synthesis = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY,
    temperature=0.0,
)
