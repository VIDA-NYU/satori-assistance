def parse_tms(raw_value: str) -> int:
    """
    Extract timestamp integer from a dash-separated string.

    Args:
        raw_value (str): A string in the format "<timestamp>-..."

    Returns:
        int: Parsed timestamp value.
    """
    return int(raw_value.split('-')[0])
