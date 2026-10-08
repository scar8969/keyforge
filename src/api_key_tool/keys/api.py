import datetime

from .generator import generate, hash_key
from .quota import QuotaCounter
from .scopes import check
from ..models import AuditLog, Key, UsageLog, db

from flask import Blueprint, jsonify, request

bp = Blueprint("keys", __name__)
_quota = QuotaCounter()

def _auth():
    """X-API-Key → Key or None (checks status + expiry)."""
    k = request.headers.get("X-API-Key", "")
    key = Key.query.filter_by(secret_hash=hash_key(k)).first()
    if not key or key.status != "active":
        return None
    if key.expires_at and key.expires_at < datetime.utcnow():
        key.status = "expired"
        db.session.commit()
        return None
    return key

@bp.post("/api/keys")
def create_key():
    d = request.get_json(force=True, silent=True) or {}
    secret = generate(d.get("prefix", "sk_live_"))
    key = Key(name=d.get("name", ""), prefix=d.get("prefix", "sk_live_"),
              secret_hash=hash_key(secret), scopes_json=str(d.get("scopes", [])),
              quota_json=str(d.get("quota", {})))
    db.session.add(key)
    db.session.flush()
    db.session.add(AuditLog(key_id=key.id, action="created",
                            detail="name=%s scopes=%s" % (key.name, key.scopes_json),
                            ip=request.remote_addr or ""))
    db.session.commit()
    return jsonify({"id": key.id, "key": secret})  # secret shown ONCE

@bp.get("/api/keys")
def list_keys():
    return jsonify({"keys": [k.to_dict() for k in Key.query.all()]})

@bp.post("/api/keys/<int:kid>/rotate")
def rotate(kid):
    k = Key.query.get_or_404(kid)
    secret = generate(k.prefix)
    k.secret_hash = hash_key(secret)
    db.session.add(AuditLog(key_id=k.id, action="rotated", detail="rotated",
                            ip=request.remote_addr or ""))
    db.session.commit()
    return jsonify({"key": secret})

@bp.post("/api/keys/<int:kid>/revoke")
def revoke(kid):
    k = Key.query.get_or_404(kid)
    k.status = "revoked"
    db.session.add(AuditLog(key_id=k.id, action="revoked", detail="status=revoked",
                            ip=request.remote_addr or ""))
    db.session.commit()
    return jsonify({"status": "revoked"})

@bp.get("/api/keys/<int:kid>/usage")
def usage(kid):
    logs = UsageLog.query.filter_by(key_id=kid).order_by(UsageLog.id.desc()).limit(100).all()
    return jsonify({"entries": [{"ts": l.ts.isoformat() if l.ts else "", "endpoint": l.endpoint,
                                 "ip": l.ip, "tokens": l.tokens} for l in logs]})

@bp.get("/api/audit")
def audit():
    entries = AuditLog.query.order_by(AuditLog.id.desc()).limit(50).all()
    return jsonify({"entries": [e.to_dict() for e in entries]})

# protected endpoint example
@bp.get("/api/users")
def users():
    key = _auth()
    if not key:
        return jsonify({"error": "unauthorized"}), 401
    if not check(key, "read:users"):
        return jsonify({"error": "forbidden"}), 403
    if not _quota.hit(key.id):
        return jsonify({"error": "rate limit exceeded"}), 429
    db.session.add(UsageLog(key_id=key.id, endpoint="/api/users", ip=request.remote_addr or ""))
    db.session.commit()
    return jsonify({"users": []})
