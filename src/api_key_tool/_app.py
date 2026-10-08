from .keys.api import bp
from .keys.generator import generate, hash_key
from .keys.scopes import SCOPE_REGISTRY
from .models import AuditLog, Key, UsageLog, db

import ast, json, os
from . import paths

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)

# Templates live next to the project root, not under web/. Without an explicit
# template_folder Flask searches web/templates and every render raises
# TemplateNotFound (HTTP 500).
paths.ensure_runtime_dirs()

def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(__name__, template_folder=str(paths.TEMPLATES_DIR),
                instance_path=str(paths.INSTANCE_DIR))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "keytool.db")
    app.secret_key = os.environ.get("SECRET_KEY", "api-key-tool-dev")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)

    @app.context_processor
    def _inject_app_name():
        return {"app_name": "API Key Tool"}

    def _scopes_of(text):
        """scopes_json is written either as JSON or as a Python repr — accept both."""
        raw = (text or "").strip()
        if not raw:
            return []
        try:
            v = json.loads(raw)
        except (TypeError, ValueError):
            try:
                v = ast.literal_eval(raw)
            except (TypeError, ValueError, SyntaxError):
                v = []
        if isinstance(v, str):
            v = [p.strip() for p in v.replace(",", " ").split() if p.strip()]
        if not isinstance(v, (list, tuple, set)):
            return []
        return sorted(str(x) for x in v)

    def _key_rows():
        rows = []
        for k in Key.query.order_by(Key.id.desc()).all():
            rows.append({"id": k.id, "name": k.name, "prefix": k.prefix,
                         "status": k.status, "created_at": k.created_at,
                         "expires_at": k.expires_at, "last_seen": k.last_seen,
                         "scopes": _scopes_of(k.scopes_json),
                         "uses": UsageLog.query.filter_by(key_id=k.id).count()})
        return rows

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "keys": Key.query.count(),
                        "usage_logs": UsageLog.query.count(),
                        "audit_logs": AuditLog.query.count()})

    @app.get("/")
    def index():
        counts = {"keys": Key.query.count(),
                  "active": Key.query.filter_by(status="active").count(),
                  "revoked": Key.query.filter_by(status="revoked").count(),
                  "uses": UsageLog.query.count()}
        return render_template("index.html", rows=_key_rows(), counts=counts,
                               audit=AuditLog.query.order_by(AuditLog.id.desc()).limit(8).all())

    @app.get("/create")
    def create_form():
        return render_template("create.html", scopes=sorted(SCOPE_REGISTRY))

    @app.post("/keys/new")
    def create_from_form():
        f = request.form
        scopes = [s for s in f.getlist("scopes") if s in SCOPE_REGISTRY]
        secret = generate(f.get("prefix") or "sk_live_")
        key = Key(name=f.get("name") or "", prefix=f.get("prefix") or "sk_live_",
                  secret_hash=hash_key(secret), scopes_json=json.dumps(scopes),
                  quota_json=json.dumps({}))
        db.session.add(key)
        db.session.flush()
        db.session.add(AuditLog(key_id=key.id, action="created",
                                detail="name=%s scopes=%s" % (key.name, scopes),
                                ip=request.remote_addr or ""))
        db.session.commit()
        flash("key #%d created — copy it now, it is shown once: %s" % (key.id, secret), "success")
        return redirect(url_for("index"))

    @app.post("/keys/<int:kid>/rotate")
    def rotate_from_form(kid):
        k = Key.query.get_or_404(kid)
        secret = generate(k.prefix)
        k.secret_hash = hash_key(secret)
        db.session.add(AuditLog(key_id=k.id, action="rotated", detail="rotated",
                                ip=request.remote_addr or ""))
        db.session.commit()
        flash("key #%d rotated — new secret (shown once): %s" % (k.id, secret), "success")
        return redirect(url_for("index"))

    @app.post("/keys/<int:kid>/revoke")
    def revoke_from_form(kid):
        k = Key.query.get_or_404(kid)
        k.status = "revoked"
        db.session.add(AuditLog(key_id=k.id, action="revoked", detail="status=revoked",
                                ip=request.remote_addr or ""))
        db.session.commit()
        flash("key #%d revoked" % k.id, "success")
        return redirect(url_for("index"))

    @app.post("/keys/<int:kid>/delete")
    def delete_from_form(kid):
        k = Key.query.get_or_404(kid)
        UsageLog.query.filter_by(key_id=k.id).delete()
        AuditLog.query.filter_by(key_id=k.id).delete()
        db.session.delete(k)
        db.session.commit()
        flash("key #%d deleted" % kid, "success")
        return redirect(url_for("index"))

    return app

app = build_app()
