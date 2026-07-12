"""
core/remediation.py

Deterministic remediation lookup -- this is the anti-hallucination
layer. Fix suggestions come from human-written rules, not the LLM.
The LLM's only job is to phrase the matched rule naturally using the
specific data; it cannot invent a fix that isn't in this table.
"""


def match_rules(row: dict, rules: list) -> list:
    """Return fixes for trusted skill-pack rules whose conditions match row."""
    matched = []
    for rule in rules:
        condition = rule["condition"]
        try:
            # Conditions are maintained in trusted local skill.yaml files, never user input.
            if eval(condition, {}, row):
                matched.append(rule["fix"])
        except Exception:
            continue
    return matched
