"""
Tests for the Concierge agent: tools + the orchestration loop + the guardrail.
A scripted (fake) planner stands in for the LLM, so no API key is needed.

Run:  uv run pytest ai_gateway_demo/test_agent.py -v
"""
import pytest

from ai_gateway_demo.agent import ConciergeAgent
from ai_gateway_demo.tools import locate, search_properties


def test_locate_returns_point_and_radius():
    loc = locate("somewhere near CMU")
    assert loc["radius_km"] > 0
    assert -90 <= loc["lat"] <= 90 and -180 <= loc["lng"] <= 180


def test_search_filters_by_radius_and_price_and_sorts():
    res = search_properties(40.4433, -79.9436, radius_km=3.0, max_price=1500)
    assert all(p["distance_km"] <= 3.0 and p["price"] <= 1500 for p in res)
    assert res == sorted(res, key=lambda p: p["distance_km"])  # nearest first


class ScriptedPlanner:
    """Fakes an LLM: locate the area -> search inside it -> answer."""

    def __init__(self):
        self.calls = 0

    def next_step(self, messages):
        self.calls += 1
        if self.calls == 1:
            return {"tool": "locate", "input": {"place": "near CMU"}}
        if self.calls == 2:
            loc = messages[-1]["content"]  # the locate result
            return {
                "tool": "search_properties",
                "input": {"lat": loc["lat"], "lng": loc["lng"], "radius_km": loc["radius_km"], "max_price": 1500},
            }
        return {"final": "Here are options near CMU under $1500."}


def test_agent_orchestrates_locate_then_search():
    out = ConciergeAgent(ScriptedPlanner()).run("find me a place near CMU under 1500")
    assert [t["tool"] for t in out["trace"]] == ["locate", "search_properties"]
    assert "CMU" in out["answer"]
    # the location-first flow actually returned some listings inside the box
    assert len(out["trace"][1]["result"]) >= 1


def test_agent_rejects_tool_outside_allowlist():
    class BadPlanner:
        def next_step(self, messages):
            return {"tool": "delete_everything", "input": {}}

    with pytest.raises(ValueError):
        ConciergeAgent(BadPlanner()).run("hi")
