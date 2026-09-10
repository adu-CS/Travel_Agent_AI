import time

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.agent.llm import llm
from app.logging_config import logger

MAX_TOOL_OUTPUT_CHARS = 3000  # guard against a bloated tool result blowing the context window


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _safe_invoke(model, messages):
    return model.invoke(messages)


def execute_react_agent(
    system_instruction: str,
    user_prompt: str,
    registered_tools: list,
    max_steps: int = 4,
    time_budget_seconds: int = 45,
) -> tuple[str, int]:
    """Runs an autonomous ReAct loop allowing the LLM to dynamically
    reason, query tools, observe output, and refine its response.

    Bounded by both max_steps and a wall-clock time budget so a slow
    model/tool call can't hang a request indefinitely.
    """
    tools_by_name = {t.name: t for t in registered_tools}
    model_with_tools = llm.bind_tools(registered_tools)

    dialogue = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_prompt),
    ]

    total_llm_invocations = 0
    start_time = time.monotonic()

    for step in range(max_steps):
        if time.monotonic() - start_time > time_budget_seconds:
            logger.warning("react_engine time budget exceeded, returning partial result")
            return "Research took too long and was cut short; results may be incomplete.", total_llm_invocations

        try:
            total_llm_invocations += 1
            ai_response = _safe_invoke(model_with_tools, dialogue)
        except Exception as e:
            logger.exception("LLM invoke failed after retries")
            return f"Research failed due to a model error: {e}", total_llm_invocations

        dialogue.append(ai_response)

        if not ai_response.tool_calls:
            return ai_response.content, total_llm_invocations

        for call in ai_response.tool_calls:
            tool_name = call["name"]
            tool_args = call["args"]
            tool_fn = tools_by_name.get(tool_name)

            if tool_fn:
                try:
                    observation = tool_fn.invoke(tool_args)
                except Exception as e:
                    logger.exception(f"Tool '{tool_name}' raised an exception")
                    observation = f"Tool '{tool_name}' failed: {e}"
            else:
                observation = f"Error: Tool '{tool_name}' not recognized."

            observation_str = str(observation)
            if len(observation_str) > MAX_TOOL_OUTPUT_CHARS:
                observation_str = observation_str[:MAX_TOOL_OUTPUT_CHARS] + "... [truncated]"

            dialogue.append(ToolMessage(content=observation_str, tool_call_id=call["id"]))

    return dialogue[-1].content, total_llm_invocations
