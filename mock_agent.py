# mock_agent.py
# Simulates tokenmaxxing: an agent that keeps calling a tool
# it shouldn't have access to, with a bloated context.

from identity import register_agent
from guard import guarded_call
from dashboard import render_dashboard

def simulate_tokenmaxxing_loop():
    """
    This agent has a small budget and read-only access.
    It tries to call a write tool in a loop. The guard catches it.
    """
    print("Registering 'code-review-bot' with read-only access and $5.00 budget...")
    register_agent(
        agent_id="code-review-bot",
        allowed_tools=["read_file", "list_files"],
        budget_usd=5.00,
    )

    print("Simulating tokenmaxxing loop...\n")
    
    # The agent tries 12 times to write a file, which it is not allowed to do.
    # It also sends a massive 40,000 token context every time.
    for i in range(12):
        result = guarded_call(
            agent_id="code-review-bot",
            task_type="refactor",
            tool="write_file",          # UNAUTHORIZED TOOL
            input_tokens=40_000,        # Bloated context window
            output_tokens=500,
        )
        
        decision = result.get('decision')
        reason = result.get('reason', 'allowed')
        
        print(f"Call {i+1:02d}: {decision} — {reason}")

    render_dashboard()

if __name__ == "__main__":
    simulate_tokenmaxxing_loop()
