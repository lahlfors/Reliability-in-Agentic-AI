package finance.trade

import future.keywords.if
import future.keywords.in

default allow := false

# Main allow rule:
# 1. Action must be "buy" or "sell"
# 2. Amount must be under the global risk limit ($50,000)
# 3. Ticker must NOT be on the restricted list
allow if {
    input.action in ["buy", "sell"]
    input.amount < 50000
    not is_restricted
}

# Restricted list logic
is_restricted if {
    input.ticker == "OIL_CORP"
    input.esg_score < 50
}

# Deny reason generation (for feedback)
violation["Global Risk Limit Exceeded (> $50k)"] if {
    input.amount >= 50000
}

violation["Restricted Asset (ESG Compliance)"] if {
    is_restricted
}

violation["Unknown Action"] if {
    not input.action in ["buy", "sell"]
}
