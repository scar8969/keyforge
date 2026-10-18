-- 🔑 API Key Tool schema
CREATE TABLE keys(id INTEGER PRIMARY KEY, name TEXT, prefix TEXT DEFAULT 'sk_live_', secret_hash TEXT, scopes_json TEXT DEFAULT '[]', quota_json TEXT DEFAULT '{}', status TEXT DEFAULT 'active', expires_at DATETIME, last_seen DATETIME, created_at DATETIME);
CREATE TABLE usage_logs(id INTEGER PRIMARY KEY, key_id INTEGER REFERENCES keys(id), ts DATETIME, endpoint TEXT, ip TEXT, tokens INTEGER DEFAULT 0);
CREATE TABLE audit_logs(id INTEGER PRIMARY KEY, key_id INTEGER REFERENCES keys(id), action TEXT, detail TEXT, ip TEXT, at DATETIME);
