"""
String manipulations, parsing, safely evaluations
"""


def safe_strip(val):
    """
    Safely strip a value, converting non-string types to string first.
    Handles None, booleans, numbers, and other types gracefully.
    """
    if val is None:
        return ""
    elif isinstance(val, bool):
        return str(val)
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, str):
        return val.strip()
    return str(val).strip()
