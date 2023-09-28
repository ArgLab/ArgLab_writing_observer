"""
This file contains constants for blacklisting/authentication rule types, their responses, priorities and patterns.

RULES_RESPONSES
A dictionary containing responses for different rule types, including:
- type (str)
- message (str)
- status_code (int)

RULES_PATTERNS
A dictionary containing patterns to match against for different rule types, specifying:
- field (str)
- patterns (arrays of regex patterns)
to apply for rule evaluation.

RULE_TYPES_BY_PRIORITIES
A list defining the priority order of rule types for sorting.
"""

ALLOW = "allow"
DENY = "deny"
DENY_FOR_TWO_DAYS = "deny_for_two_days"

# Responses for different rule types
RULES_RESPONSES = {
    ALLOW: {
        "type": ALLOW,
        "msg": "Allow events to be sent",
        "status_code": 200
    },
    DENY: {
        "type": DENY,
        "msg": "Deny events from being sent",
        "status_code": 403
    },
    DENY_FOR_TWO_DAYS: {
        "type": DENY_FOR_TWO_DAYS,
        "msg": "Deny events from being sent temporarily for two days",
        "status_code": 403
    }
}

# Patterns to match against for different rule types
RULES_PATTERNS = {
    DENY: [
        {
            "field": "email",
            "patterns": ["^.*@ncsu.edu"]
        },
        {
            "field": "google_id",
            "patterns": ["1234"]
        }
    ],
    DENY_FOR_TWO_DAYS: [
        {
            "field": "email",
            "patterns": ["^.*@ncsu.edu"]
        }
    ]
}

# Priority order of rule types for sorting
RULE_TYPES_BY_PRIORITIES = [DENY, DENY_FOR_TWO_DAYS]
