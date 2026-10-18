import argparse
import json
import sys


def _app():
    """Import the Flask app lazily so --help works without the web deps loaded."""
    from ._app import app

    return app


def cmd_create(args):
    from .keys.generator import generate, hash_key
    from .models import AuditLog, Key, db

    app = _app()
    with app.app_context():
        secret = generate(args.prefix)
        k = Key(
            name=args.name,
            prefix=args.prefix,
            secret_hash=hash_key(secret),
            scopes_json=json.dumps(list(args.scopes)),
        )
        db.session.add(k)
        db.session.flush()
        db.session.add(
            AuditLog(
                key_id=k.id, action="created", detail="via cli scopes=%s" % (list(args.scopes),)
            )
        )
        db.session.commit()
        print(secret)  # shown once
    return 0


def cmd_list(args):
    from .models import Key

    app = _app()
    with app.app_context():
        rows = [k.to_dict() for k in Key.query.order_by(Key.id.desc()).all()]
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            print(
                "#%-4s %-20s %-10s %-9s %s"
                % (r["id"], r["name"], r["status"], r["prefix"], r["scopes"])
            )
    return 0


def cmd_rotate(args):
    from .keys.generator import generate, hash_key
    from .models import AuditLog, Key, db

    app = _app()
    with app.app_context():
        k = Key.query.filter_by(id=args.key_id).first()
        if k is None:
            print("no key with id %d" % args.key_id, file=sys.stderr)
            return 2
        secret = generate(k.prefix)
        k.secret_hash = hash_key(secret)
        db.session.add(AuditLog(key_id=k.id, action="rotated", detail="via cli"))
        db.session.commit()
        print(secret)  # shown once
    return 0


def cmd_revoke(args):
    from .models import AuditLog, Key, db

    app = _app()
    with app.app_context():
        k = Key.query.filter_by(id=args.key_id).first()
        if k is None:
            print("no key with id %d" % args.key_id, file=sys.stderr)
            return 2
        k.status = "revoked"
        db.session.add(AuditLog(key_id=k.id, action="revoked", detail="via cli"))
        db.session.commit()
        print("revoked #%d" % k.id)
    return 0


def main():
    p = argparse.ArgumentParser(prog="apikey", description="API key manager")
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("create", help="mint a new key and print the secret once")
    c.add_argument("--name", required=True)
    c.add_argument("--prefix", default="sk_live_")
    c.add_argument("--scopes", nargs="+", default=["read:users"])
    l = sub.add_parser("list", help="list stored keys")
    l.add_argument("--json", action="store_true")
    r = sub.add_parser("rotate", help="rotate a key secret")
    r.add_argument("key_id", type=int)
    v = sub.add_parser("revoke", help="revoke a key")
    v.add_argument("key_id", type=int)
    args = p.parse_args()
    if args.cmd == "create":
        return cmd_create(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "rotate":
        return cmd_rotate(args)
    if args.cmd == "revoke":
        return cmd_revoke(args)
    p.print_help()
    return 1
