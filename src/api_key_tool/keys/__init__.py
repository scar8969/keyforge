"""keys - API-key generation, scope checks, quotas and the /api/keys blueprint.

Contents
    generator.py  generate / hash_key / verify_key
    scopes.py     SCOPE_REGISTRY, parse, check
    quota.py      QuotaCounter
    api.py        the keys blueprint mounted by web/app.py
    models.py     compatibility shim, see below

The SQLAlchemy handle and the Key/UsageLog/AuditLog models are declared once, in
the PROJECT-ROOT models.py, because web/app.py, wsgi.py and cli.py need them too.
db therefore lives in that root module, and the correct import inside this
package is

    from models import db, Key

and NOT 'from . import db', which would look for a non-existent keys/db.py.
The handle is re-exported here only so 'from keys import db' keeps working.
"""

from ..models import AuditLog, Key, UsageLog, db

__all__ = ["AuditLog", "Key", "UsageLog", "db"]
