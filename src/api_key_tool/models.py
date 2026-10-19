from flask_sqlalchemy import SQLAlchemy

from .clock import utcnow

db = SQLAlchemy()


class Key(db.Model):
    __tablename__ = "keys"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), default="")
    prefix = db.Column(db.String(32), default="sk_live_")
    secret_hash = db.Column(db.String(64), default="")
    scopes_json = db.Column(db.Text, default="[]")
    quota_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(16), default="active")  # active|revoked|expired
    expires_at = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "scopes": self.scopes_json,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else "",
            "last_seen": self.last_seen.isoformat() if self.last_seen else "",
        }


class UsageLog(db.Model):
    __tablename__ = "usage_logs"
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey("keys.id"), index=True)
    ts = db.Column(db.DateTime, default=utcnow)
    endpoint = db.Column(db.String(128), default="")
    ip = db.Column(db.String(64), default="")
    tokens = db.Column(db.Integer, default=0)


class AuditLog(db.Model):
    """Append-only trail of every mutating key operation."""

    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey("keys.id"), index=True)
    action = db.Column(db.String(32), default="")  # created|rotated|revoked
    detail = db.Column(db.String(256), default="")
    ip = db.Column(db.String(64), default="")
    at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "key_id": self.key_id,
            "action": self.action,
            "detail": self.detail,
            "ip": self.ip,
            "at": self.at.isoformat() if self.at else "",
        }
