# dashboard.py
# One dashboard. FinOps and SecOps read the same numbers.

from identity import AGENT_REGISTRY

def render_dashboard():
    print("\n" + "=" * 60)
    print("TOKENMAXXING-GUARD | UNIFIED FINOPS + SECOPS DASHBOARD")
    print("=" * 60)
    
    if not AGENT_REGISTRY:
        print("No agents registered yet.")
        return
        
    for agent_id, a in AGENT_REGISTRY.items():
        status = "OK"
        
        # FinOps check
        if a["spent_usd"] > a["budget_usd"] * 0.8:
            status = "BUDGET_WARNING"
            
        # SecOps check
        if a["anomalies"]:
            status = "ANOMALY"
            
        print(f"\nAgent: {a['agent_id']}")
        print(f"  Budget:  ${a['budget_usd']:.2f}")
        print(f"  Spent:   ${a['spent_usd']:.4f}")
        print(f"  Calls:   {a['call_count']}")
        print(f"  Status:  {status}")
        
        if a["anomalies"]:
            print(f"  Alerts:  {a['anomalies']}")
            
    print("\n" + "=" * 60)
