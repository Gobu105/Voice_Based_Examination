def required_fields(data, keys):
    return [key for key in keys if not data.get(key)]


def is_positive_int(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False
