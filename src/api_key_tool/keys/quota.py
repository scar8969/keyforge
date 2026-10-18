import json
from datetime import date


class QuotaCounter:
    def __init__(self):
        self._hits = {}

    def hit(self, key_id, tokens=0):
        quota = self.quota_for(key_id)
        today = date.today().isoformat()
        cur_date, count = self._hits.get(key_id, (today, 0))
        if cur_date != today:
            cur_date, count = today, 0
        if quota.get("requests") and count >= quota["requests"]:
            return False
        self._hits[key_id] = (today, count + 1)
        return True

    def reset_daily(self):
        self._hits.clear()

    def quota_for(self, key_id):
        """Quota limits for a key; an unknown or unreadable key has none.

        Authentication decides whether a key exists; this counter only
        enforces limits, so a missing row must not take the request path down.
        """
        from ..models import Key

        try:
            key = Key.query.get(key_id)
        except Exception:
            return {}
        if key is None:
            return {}
        try:
            return json.loads(key.quota_json or "{}")
        except (TypeError, ValueError):
            return {}
