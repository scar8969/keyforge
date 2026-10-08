== curl ==
# POST /api/keys  {"name":"ci-deploy","prefix":"sk_live_","scopes":["read:users"],"quota":{"requests":1000}}
# GET  /api/keys
# POST /api/keys/1/rotate | /revoke
# GET  /api/keys/1/usage
# GET  /api/users -H "X-API-Key: sk_live_…"
# CLI: apikey create --name ci-deploy --scopes read:users

== session plan ==
# Session 1: generator + scopes + quota → tests
# Session 2: api CRUD + auth middleware + audit → tests
# Session 3: web templates + cli → screenshots → README → CI/Docker/Pages → tag
