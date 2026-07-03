"""
Housing Concierge: a minimal tool-using agent that "carries the user through"
finding housing by orchestrating the app's capabilities as tools.

Design:
- the ORCHESTRATION LOOP is your code + tools (below);
- the LLM is a SWAPPABLE component behind the `Planner` interface;
- guardrails (the tool allowlist) live in code, not the prompt.

Loop: ask the planner what to do -> if it wants a tool, run it and feed the
result back -> repeat until the planner returns a final answer.
"""
import os
from typing import Protocol

from .tools import TOOLS


class Planner(Protocol):
    def next_step(self, messages: list[dict]) -> dict:
        """Return {'tool': name, 'input': {...}} to call a tool, or {'final': text} to stop."""
        ...


class ConciergeAgent:
    def __init__(self, planner: Planner, max_steps: int = 6):
        self.planner = planner
        self.max_steps = max_steps

    def run(self, user_message: str) -> dict:
        messages: list[dict] = [{"role": "user", "content": user_message}]
        trace: list[dict] = []
        for _ in range(self.max_steps):
            step = self.planner.next_step(messages)
            if "final" in step:
                return {"answer": step["final"], "trace": trace}
            name = step["tool"]
            args = step.get("input", {})
            if name not in TOOLS:  # guardrail: never call a tool outside the allowlist
                raise ValueError(f"unknown tool: {name}")
            result = TOOLS[name]["fn"](**args)
            trace.append({"tool": name, "input": args, "result": result})
            messages.append({"role": "tool", "name": name, "content": result})
        return {"answer": "stopped: max steps reached", "trace": trace}


class LLMPlanner:
    """Provider-agnostic planner backed by a real LLM's function-calling.

    Default implementation uses Google Gemini; to use OpenAI or Claude instead,
    only `_ask` changes (the tool schemas + loop stay identical). Needs the
    provider SDK + its API key. NOT exercised by tests.
    """

    MODEL = "gemini-2.0-flash"
    SYSTEM = (
        "You are a housing concierge for young renters. FIRST establish the location "
        "area with `locate`, THEN find places with `search_properties` inside it. "
        "Always respect the user's budget. Be concise."
    )

    def __init__(self, model: str | None = None):
        self.model = model or self.MODEL

    def next_step(self, messages: list[dict]) -> dict:
        return self._ask(messages)

    # --- the only provider-specific part; swap this method to change LLM vendor ---
    def _ask(self, messages: list[dict]) -> dict:
        import google.generativeai as genai  # lazy import so the module has no hard dep

        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        gemini_tools = [
            {
                "function_declarations": [
                    {
                        "name": t["schema"]["name"],
                        "description": t["schema"]["description"],
                        "parameters": t["schema"]["input_schema"],
                    }
                    for t in TOOLS.values()
                ]
            }
        ]
        model = genai.GenerativeModel(self.model, system_instruction=self.SYSTEM, tools=gemini_tools)
        resp = model.generate_content(messages[0]["content"])
        for part in resp.candidates[0].content.parts:
            call = getattr(part, "function_call", None)
            if call:
                return {"tool": call.name, "input": dict(call.args)}
        return {"final": resp.text}
