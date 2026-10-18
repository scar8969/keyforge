import json

SCOPE_REGISTRY = {"read:users", "write:users", "read:keys", "admin"}


def parse(scopes_str):
    try:
        return set(json.loads(scopes_str))
    except Exception:
        return set()


def check(key, needed):
    scopes = parse(key.scopes_json)
    if "admin" in scopes:
        return True
    return needed in scopes
