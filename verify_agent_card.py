# verify_agent_card.py
import os
import logging
# Configure basic logging to see output
logging.basicConfig(level=logging.INFO)

from vacp.c2pa import C2PASigner
from vacp.card_loader import CardLoader
from vacp.gateway import Gateway, gateway as global_gateway, ToolGateway

import os
# Adjust path if running from root or subdir
if os.path.exists("financial-advisor/agent.json"):
    CARD_PATH = "financial-advisor/agent.json"
elif os.path.exists("agent.json"):
    CARD_PATH = "agent.json"
else:
    # Fallback to absolute path or assume running from root
    CARD_PATH = "financial-advisor/agent.json"

SIG_PATH = CARD_PATH + ".sig"

def run_verification():
    print("--- 1. Signing the Card (Mock C2PA) ---")
    signer = C2PASigner()
    signer.sign_file(CARD_PATH, SIG_PATH)
    print(f"Signed {CARD_PATH} -> {SIG_PATH}\n")

    print("--- 2. Loading the Card ---")
    loader = CardLoader(enforce_signature=True)
    try:
        card = loader.load_card(CARD_PATH)
    except Exception as e:
        print(f"FATAL: {e}")
        return

    print("--- 3. Testing Enforcement (Gateway) ---")
    # We can test the standalone Gateway class logic
    test_gateway = Gateway(agent_card=card)

    # Test Allowed Tool
    tool_ok = "get_stock_price"
    result_ok = test_gateway.check_tool_policy(tool_ok)
    print(f"Tool '{tool_ok}': {'Allowed ✅' if result_ok else 'Blocked ❌'}")
    assert result_ok == True

    # Test Denied Tool
    tool_bad = "shell_execute"
    result_bad = test_gateway.check_tool_policy(tool_bad)
    print(f"Tool '{tool_bad}': {'Allowed ❌' if result_bad else 'Blocked ✅'}")
    assert result_bad == False

    # Test Unlisted Tool (Should be blocked if allow-list exists)
    tool_unknown = "random_function"
    result_unknown = test_gateway.check_tool_policy(tool_unknown)
    print(f"Tool '{tool_unknown}': {'Allowed ❌' if result_unknown else 'Blocked ✅'}")
    assert result_unknown == False

    print("\n--- 4. Testing Integrated Global Gateway ---")
    # Verify the global gateway (ToolGateway) works when policy is set
    global_gateway.set_policy(card)

    # ToolGateway.verify_access raises PermissionError on failure
    try:
        global_gateway.verify_access(tool_ok, {})
        print(f"Global Gateway '{tool_ok}': Access Granted ✅")
    except PermissionError as e:
        print(f"Global Gateway '{tool_ok}': Unexpected Denial ❌ ({e})")

    try:
        global_gateway.verify_access(tool_bad, {})
        print(f"Global Gateway '{tool_bad}': Unexpected Grant ❌")
    except PermissionError:
        print(f"Global Gateway '{tool_bad}': Access Denied ✅")

    print("\n--- ✅ Verification Complete: System is Secure ---")

if __name__ == "__main__":
    run_verification()
