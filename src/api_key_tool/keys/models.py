"""Compatibility shim: keys/models.py is NOT a second model module.

The real models (and the SQLAlchemy handle) live in the PROJECT-ROOT models.py,
one directory up, because web/app.py, wsgi.py and cli.py all import them from
there. This module exists only so that the sibling form

    from .models import Key          # inside keys/*.py

resolves instead of raising ModuleNotFoundError: No module named 'keys.models'.
New code in this package should import from the root module directly:

    from models import Key, UsageLog, db
"""

from ..models import AuditLog, Key, UsageLog, db

__all__ = ["AuditLog", "Key", "UsageLog", "db"]
