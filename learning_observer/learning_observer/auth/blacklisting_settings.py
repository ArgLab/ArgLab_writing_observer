"""
This file contains constants, patterns, and functions related to blacklisting/authentication rules and responses.

RULES_RESPONSES
A dictionary containing responses for different rule types, including:
- type (str)
- msg (str)
- status_code (int)

RULE_TYPES_BY_PRIORITIES
A list defining the priority order of rule types for sorting.

load_patterns(file_path='blacklisting_patterns.yaml')
A function that loads blacklisting patterns from a YAML file and returns them as a dictionary.

authenticate_payload(payload)
A function that evaluates a payload against a set of rules and determines the authentication response.
"""


import os
import re
import yaml
from learning_observer.log_event import debug_log
import learning_observer.paths as paths

ALLOW = "allow"
DENY = "deny"
DENY_FOR_TWO_DAYS = "deny_for_two_days"

# Priority order of rule types for sorting
RULE_TYPES_BY_PRIORITIES = [DENY, DENY_FOR_TWO_DAYS]

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


def load_patterns(file_name='blacklisting_patterns.yaml'):
    """
    Load blacklisting patterns from a YAML config file.

    Args:
        file_name (str, optional): The name of the YAML file containing the blacklisting patterns.
            Defaults to 'blacklisting_patterns.yaml'.

    Returns:
        dict: A dictionary containing the loaded blacklisting patterns, or an empty dictionary
            if the file is not found or there is an error loading the patterns.
    """
    pathname = os.path.join(os.path.dirname(paths.base_path()), 'learning_observer/auth', file_name)
    try:
        with open(pathname, 'r') as file:
            rules_patterns = yaml.safe_load(file)
        debug_log("Blacklisting patterns loaded")
        return rules_patterns
    except FileNotFoundError:
        debug_log(f"No blacklisting patterns file added: '{pathname}' not found.")
        return {}


def authenticate_payload(payload):
    '''
    Evaluate a payload against a set of rules and determine the authentication response.

    This function iterates through a list of rules for various fields in the payload.
    For each field, it checks if the value matches any of the specified patterns.
    If a match is found, the associated rule type is added to a list of failed rule types.
    The failed rule types are then sorted by priority, and the highest priority failed rule
    determines the authentication response.

    If no rules fail, the function returns the 'allow' response.

    Args:
        payload (dict): The payload containing data to be authenticated.

    Returns:
        str: The authentication response based on the payload and rule evaluation.
    '''
    RULES_PATTERNS = load_patterns()
    failed_rule_types = []  # A list to store rule types that the payload fails to comply with
    for rule_type, rules in RULES_PATTERNS.items():
        for rule in rules:
            field = rule["field"]  # Get the field to be looked up in the payload
            patterns = rule["patterns"]  # Get the patterns to match against for the payload value of the field
            value = payload.get(field)  # Get the value of the field from the payload
            if value:
                for pattern in patterns:
                    # If there is a pattern match, add the rule type to the failed list
                    if re.match(pattern, value):
                        failed_rule_types.append(rule_type)

    # Sort the failed rule types based on their priority order
    sorted_failed_rule_types = sorted(failed_rule_types, key=RULE_TYPES_BY_PRIORITIES.index)
    # Determine the response key based on the highest priority failed rule, or 'allow' if no rule failed
    response_key = sorted_failed_rule_types[0] if sorted_failed_rule_types else ALLOW
    # Return the appropriate response based on the response key
    return RULES_RESPONSES[response_key]
