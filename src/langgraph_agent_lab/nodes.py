"""Node functions for the LangGraph workflow.

Each function receives AgentState and returns a partial state update dict.
Do NOT mutate input state — return new values only.

LLM REQUIREMENT:
- classify_node MUST use a real LLM call (structured output for intent classification)
- answer_node MUST use a real LLM call (grounded response generation)
- evaluate_node SHOULD use LLM-as-judge (bonus points; heuristic acceptable for base score)
"""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, Field

from .llm import get_llm
from .state import AgentState, ApprovalDecision, Route, make_event


class IntentClassification(BaseModel):
    """Structured output contract used by the classifier LLM."""

    route: Literal["simple", "tool", "missing_info", "risky", "error"]
    rationale: str = Field(description="Short reason based on the routing policy")


class ToolEvaluation(BaseModel):
    """Structured output contract for the optional LLM quality judge."""

    result: Literal["success", "needs_retry"]
    rationale: str = Field(description="Why the tool result is or is not usable")


def _content_text(response: Any) -> str:
    """Normalize LangChain provider responses to a plain string."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


# ─── EXAMPLE: working node (provided for reference) ──────────────────
def intake_node(state: AgentState) -> dict:
    """Normalize raw query. This node is provided as a working example."""
    query = state.get("query", "").strip()
    return {
        "query": query,
        "messages": [f"intake:{query[:40]}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }


def classify_node(state: AgentState) -> dict[str, Any]:
    """Classify the query into a route using an LLM.

    *** MUST use a real LLM call — keyword-only heuristics will lose points. ***

    Use .with_structured_output() or equivalent to get reliable enum classification.
    The LLM should classify into one of: simple, tool, missing_info, risky, error.

    Hints:
    - See llm.py for the get_llm() helper
    - Use Pydantic model or TypedDict with .with_structured_output()
    - Set risk_level to "high" for risky routes, "low" otherwise
    - Priority guide: risky > tool > missing_info > error > simple

    Return: {"route": str, "risk_level": str, "events": [make_event(...)]}
    """
    policy = """You route support tickets into exactly one category.
Apply this priority when more than one category could fit:
1. risky: requests that cause side effects (refund, delete, cancel, send, modify).
2. tool: information lookup or search that requires an external system.
3. missing_info: vague or incomplete requests without enough actionable context.
4. error: reports of timeouts, crashes, outages, service failures, or processing errors.
5. simple: informational support questions answerable without a tool.
Do not key off scenario IDs. Classify only the meaning of the user's query."""
    classifier = get_llm(temperature=0.0).with_structured_output(IntentClassification)
    result = classifier.invoke([("system", policy), ("human", state.get("query", ""))])
    route = result.route if isinstance(result, IntentClassification) else str(result["route"])
    risk_level = "high" if route == Route.RISKY.value else "low"
    return {
        "route": route,
        "risk_level": risk_level,
        "events": [make_event("classify", "completed", f"classified as {route}")],
    }


def tool_node(state: AgentState) -> dict[str, Any]:
    """Execute a mock tool call.

    Simulate transient failures for error-route scenarios to test retry loops.

    Requirements:
    - Read current attempt count from state
    - If route is "error" and attempt < 2: return error result (string containing "ERROR")
    - Otherwise: return a mock success result string
    - Append result to tool_results list

    Return: {"tool_results": [result_string], "events": [make_event(...)]}
    """
    attempt = int(state.get("attempt", 0))
    query = state.get("query", "")
    if state.get("route") == Route.ERROR.value and attempt < 2:
        result = f"ERROR: transient support-tool failure on attempt {attempt + 1}"
        event_type = "failed"
    else:
        result = f"SUCCESS: mock support tool completed the request: {query}"
        event_type = "completed"
    return {
        "tool_results": [result],
        "events": [make_event("tool", event_type, result, attempt=attempt)],
    }


def evaluate_node(state: AgentState) -> dict[str, Any]:
    """Evaluate tool results — the retry-loop gate.

    Check whether the latest tool result is satisfactory or needs retry.

    SHOULD use LLM-as-judge for bonus points. Heuristic (e.g., check for "ERROR" substring)
    is acceptable for base score.

    Requirements:
    - Read the latest entry from tool_results
    - Set evaluation_result to "needs_retry" or "success"
    - This field drives route_after_evaluate conditional edge

    Note: You may need to add 'evaluation_result' to AgentState if not present.

    Return: {"evaluation_result": str, "events": [make_event(...)]}
    """
    latest = (state.get("tool_results") or [""])[-1]
    evaluation = "needs_retry" if "ERROR" in latest.upper() else "success"
    rationale = "deterministic safety gate"

    # The LLM judge is opt-in because routing must remain deterministic in CI. If it
    # is enabled but unavailable, the conservative ERROR gate above still applies.
    if os.getenv("LLM_EVALUATE", "").lower() in {"1", "true", "yes"}:
        try:
            judge = get_llm(temperature=0.0).with_structured_output(ToolEvaluation)
            judged = judge.invoke(
                [
                    ("system", "Judge whether this tool result is usable. Any ERROR needs retry."),
                    ("human", latest),
                ]
            )
            evaluation = (
                judged.result if isinstance(judged, ToolEvaluation) else str(judged["result"])
            )
            rationale = "LLM quality judge"
        except Exception as exc:  # keep the bounded retry path operational on provider failures
            rationale = f"LLM judge unavailable; used safety gate ({type(exc).__name__})"

    return {
        "evaluation_result": evaluation,
        "events": [make_event("evaluate", "completed", evaluation, rationale=rationale)],
    }


def answer_node(state: AgentState) -> dict[str, Any]:
    """Generate a final response using an LLM.

    *** MUST use a real LLM call — hardcoded strings will lose points. ***

    The LLM should generate a helpful response grounded in available context:
    - tool_results (if any)
    - approval decision (if risky route)
    - original query

    Return: {"final_answer": str, "events": [make_event(...)]}
    """
    tool_context = "\n".join(state.get("tool_results") or []) or "No tool was needed."
    approval = state.get("approval")
    prompt = f"""User query: {state.get("query", "")}
Classified route: {state.get("route", "")}
Tool context:
{tool_context}
Approval decision: {approval or "not applicable"}

Write a concise, helpful support response. Treat tool context as the only factual
external-system evidence. Never claim an action succeeded unless a SUCCESS result says so."""
    response = get_llm(temperature=0.0).invoke(
        [
            ("system", "You are a careful support agent. Ground the answer in supplied context."),
            ("human", prompt),
        ]
    )
    answer = _content_text(response)
    if not answer:
        raise RuntimeError("LLM returned an empty answer")
    return {
        "final_answer": answer,
        "messages": [f"assistant:{answer}"],
        "events": [make_event("answer", "completed", "grounded answer generated")],
    }


def ask_clarification_node(state: AgentState) -> dict[str, Any]:
    """Ask for missing information instead of hallucinating.

    Generate a specific clarification question based on the vague/incomplete query.

    Note: You may need to add 'pending_question' to AgentState if not present.

    Return: {"pending_question": str, "final_answer": str, "events": [make_event(...)]}
    """
    query = state.get("query", "").strip()
    approval = state.get("approval") or {}
    if approval.get("approved") is False:
        question = "The proposed action was not approved. What safer alternative would you like?"
    else:
        question = (
            f"Could you provide the affected account/order and the desired outcome for: “{query}”?"
        )
    return {
        "pending_question": question,
        "final_answer": question,
        "events": [make_event("clarify", "completed", "clarification requested")],
    }


def risky_action_node(state: AgentState) -> dict[str, Any]:
    """Prepare a risky action for human approval.

    Describe the proposed action and why it requires approval.

    Note: You may need to add 'proposed_action' to AgentState if not present.

    Return: {"proposed_action": str, "events": [make_event(...)]}
    """
    action = (
        f"Proposed support action: {state.get('query', '')}. "
        "Approval is required because this request may change customer data, "
        "money, or communications."
    )
    return {
        "proposed_action": action,
        "events": [make_event("risky_action", "prepared", "action awaiting approval")],
    }


def approval_node(state: AgentState) -> dict[str, Any]:
    """Human-in-the-loop approval step.

    Default behavior: mock approval (approved=True) so tests and CI run offline.
    Extension: if env LANGGRAPH_INTERRUPT=true, use langgraph.types.interrupt() for real HITL.

    Return the normalized approval mapping and an append-only audit event.
    """
    decision: Any
    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() in {"1", "true", "yes"}:
        from langgraph.types import interrupt

        decision = interrupt(
            {
                "type": "approval_required",
                "thread_id": state.get("thread_id"),
                "proposed_action": state.get("proposed_action"),
            }
        )
        if isinstance(decision, bool):
            decision = {"approved": decision, "reviewer": "human", "comment": ""}
    else:
        decision = {"approved": True, "reviewer": "mock-reviewer", "comment": "CI default"}

    approval = ApprovalDecision.model_validate(decision).model_dump()
    status = "approved" if approval["approved"] else "rejected"
    return {
        "approval": approval,
        "events": [
            make_event("approval", status, f"action {status}", reviewer=approval["reviewer"])
        ],
    }


def retry_or_fallback_node(state: AgentState) -> dict[str, Any]:
    """Record a retry attempt.

    Increment the attempt counter and log the transient failure.

    Requirements:
    - Read current attempt from state, increment by 1
    - Add an error message to errors list
    - Return updated attempt count

    Return: {"attempt": int, "errors": [str], "events": [make_event(...)]}
    """
    attempt = int(state.get("attempt", 0)) + 1
    error = f"Transient failure recorded; retry attempt {attempt} of {state.get('max_attempts', 3)}"
    return {
        "attempt": attempt,
        "errors": [error],
        "events": [make_event("retry", "scheduled", error, attempt=attempt)],
    }


def dead_letter_node(state: AgentState) -> dict[str, Any]:
    """Handle unresolvable failures after max retries exceeded.

    This is the third layer: retry → fallback → dead letter.
    Log the failure and set a final_answer explaining that the request could not be completed.

    Return: {"final_answer": str, "events": [make_event(...)]}
    """
    answer = (
        "The request could not be completed after the configured retry limit. "
        "It has been moved to the support dead-letter queue for manual investigation."
    )
    return {
        "final_answer": answer,
        "events": [make_event("dead_letter", "failed", answer, attempts=state.get("attempt", 0))],
    }


def finalize_node(state: AgentState) -> dict[str, Any]:
    """Emit a final audit event. All routes must pass through here before END.

    Return: {"events": [make_event("finalize", "completed", "workflow finished")]}
    """
    return {"events": [make_event("finalize", "completed", "workflow finished")]}
