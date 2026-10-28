"""How to put the guard in front of a real model call.

Run:  python examples/integrate.py
Swap `fake_model_call` for your provider SDK; everything else stays the same.
"""

from pathlib import Path

from tokenmaxxing_guard import AuditLog, Guard

POLICY = Path(__file__).with_name("policy.json")


def fake_model_call(tier: str, prompt: str):
    """Stand-in for an LLM SDK call. Returns (text, input_tokens_used, output_tokens_used)."""
    return f"[{tier}] ok", len(prompt) // 4, 120


def run_agent_step(guard: Guard, agent_id: str, task: str, tool: str, prompt: str) -> str:
    verdict = guard.check(agent_id, task, tool, input_tokens=len(prompt) // 4, output_tokens=500)
    if not verdict.allowed:
        # Fail closed: never call the model or the tool on a block.
        return f"BLOCKED ({verdict.decision.value}): {verdict.reason}"

    text, used_in, used_out = fake_model_call(verdict.tier, prompt)
    guard.settle(verdict.call_id, used_in, used_out)  # replace the estimate with real usage
    return text


if __name__ == "__main__":
    guard = Guard.from_policy(POLICY, audit=AuditLog("audit.jsonl"))
    print(run_agent_step(guard, "code-review-bot", "summarize", "read_file", "x" * 4_000))
    print(run_agent_step(guard, "code-review-bot", "summarize", "create_tag", "x" * 4_000))
    print(run_agent_step(guard, "someone-unregistered", "summarize", "read_file", "hi"))
