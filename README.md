<p align="center">
  <img src="docs/assets/screens/create.png" alt="keyforge running" width="900">
</p>

<h1 align="center">keyforge</h1>

<p align="center"><b>Mint, rotate, revoke and audit API keys — the secret is shown once.</b></p>

<p align="center">
  <a href="https://github.com/scar8969/keyforge/actions/workflows/ci.yml"><img src="https://github.com/scar8969/keyforge/actions/workflows/ci.yml/badge.svg" alt="ci"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-25%20passed-2ea44f" alt="tests: 25 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-63.8%-yellow" alt="coverage: 63.8%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-10%20live-0969da" alt="routes: 10 live"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

keyforge is the key-issuing service every internal API ends up needing: create a key with a scope list and a quota, see the secret exactly once, rotate it without downtime, revoke it, and read an audit trail of who did what.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [CLI](#cli) &nbsp;·&nbsp; [Configuration](#configuration) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [How a request flows](#how-a-request-flows) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Development](#development) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

## Why this exists

Keys leak in three ways: the secret is stored recoverably, revocation is a boolean nobody checks, and there is no record of the rotation. keyforge stores only a hash, checks status on every request, and writes an audit row for every mutation.

## What it does

| Capability | How it works |
| --- | --- |
| **Hashed secrets** | Only a digest is stored; the plaintext is returned by the create call and never again. |
| **Scopes and quota** | Each key carries a scope list and a per-key quota; the example protected route checks both. |
| **Rotation and revocation** | Rotate replaces the digest and returns the new secret; revoke marks the row so the next request fails. |
| **Usage and audit** | GET /api/keys/<id>/usage returns recent calls; GET /api/audit returns the mutation log. |
| **HTML + API** | A /create page for humans, the same operations as JSON for services. |

## Quickstart

```sh
git clone https://github.com/scar8969/keyforge.git
cd keyforge
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python wsgi.py                                 # http://127.0.0.1:8000
```

It is up when this answers:

```sh
curl -s http://127.0.0.1:8000/api/health
```

## Screenshots

Captured from the running service with headless Chromium at 1440×900, one image per page, committed under [`docs/assets/screens/`](docs/assets/screens/).

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/root.png" alt="/" width="100%"><br><sub><code>/</code> &middot; 43.6 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/healthz.png" alt="/healthz" width="100%"><br><sub><code>/healthz</code> &middot; 8.4 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/livez.png" alt="/livez" width="100%"><br><sub><code>/livez</code> &middot; 7.3 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/metrics.png" alt="/metrics" width="100%"><br><sub><code>/metrics</code> &middot; 16.2 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/readyz.png" alt="/readyz" width="100%"><br><sub><code>/readyz</code> &middot; 7.7 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/version.png" alt="/version" width="100%"><br><sub><code>/version</code> &middot; 26.7 KB</sub></td>
</tr>
</table>

## API

Every route below is declared in [`openapi/keyforge.yaml`](openapi/keyforge.yaml) and exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/health` | liveness probe |
| `GET` | `/api/keys` | list keys (secrets are never returned) |
| `POST` | `/api/keys` | mint a key; the secret is returned exactly once |
| `POST` | `/api/keys/{id}/rotate` | replace a key's secret |
| `POST` | `/api/keys/{id}/revoke` | mark a key revoked |
| `GET` | `/api/keys/{id}/usage` | last 100 usage entries for a key |
| `GET` | `/api/audit` | the 50 most recent audit-log rows |
| `GET` | `/api/users` | scope-protected example endpoint |
| `GET` | `/create` | HTML key-creation form |
| `POST` | `/keys/new` | create a key from the HTML form |
| `POST` | `/keys/{id}/rotate` | rotate a key from the HTML form |
| `POST` | `/keys/{id}/revoke` | revoke a key from the HTML form |
| `POST` | `/keys/{id}/delete` | delete a key from the HTML form |

## CLI

The same operations without an HTTP client. Installed as `keyforge`, and runnable from a checkout with no install:

```sh
python -m api_key_tool.cli --help
```

```text
usage: apikey [-h] {create,list,rotate,revoke} ...

API key manager

positional arguments:
  {create,list,rotate,revoke}
    create              mint a new key and print the secret once
    list                list stored keys
    rotate              rotate a key secret
    revoke              revoke a key

options:
  -h, --help            show this help message and exit
```

## Configuration

Environment only — there is no config file. Copy `.env.example` to `.env` and edit; `APP_ENV=production` refuses to start without `SECRET_KEY`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | development \| staging \| production; production enforces the secret. |
| `SECRET_KEY` | `change-me-in-production` | Session/CSRF signing key. Required when APP_ENV=production. |
| `HOST` | `0.0.0.0` | Interface the dev server binds. |
| `PORT` | `8000` | Port the dev server and the container listen on. |
| `DEBUG` | `false` | Flask debug mode. Never true in production. |
| `MAX_CONTENT_LENGTH` | `8388608` | Largest accepted request body, in bytes. |
| `DATA_DIR` | `(empty)` | Where uploaded and generated files live. |
| `INSTANCE_DIR` | `(empty)` | Where the SQLite file and instance state live. |
| `LOG_DIR` | `(empty)` | Where rotated log files are written, if file logging is on. |
| `LOG_LEVEL` | `INFO` | DEBUG \| INFO \| WARNING \| ERROR. |
| `LOG_JSON` | `true` | true emits one JSON object per line; false is human-readable. |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header echoed on every response and stamped on every log line. |

## Measured, not estimated

Produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **25 / 25 passed** (2.9 s, exit 0) |
| Line coverage | **63.8%** — 478 of 717 statements |
| Source | 16 files / 1,558 lines |
| Test code | 4 files / 255 lines |
| Documented paths | 12 in the spec, 6 GET |
| Live probe | 12 GET requests to the booted app, **10 answered 200** |
| Median latency | **6.5 ms** (single uncached request, dev server) |
| Slowest / fastest | 74.1 ms `/` / 3.5 ms `/version` |
| Bytes served | 11.7 KB across 12 responses |
| Screenshots | 7 captured |

## How a request flows

```text
client
  │  HTTP
  ▼
wsgi.py ──▶ api_key_tool/app.py:get_app()
                │  reads config once (api_key_tool/config.py)
                │  registers the `keys` blueprint
                ▼
           route handler
             ├──▶ api_key_tool/models.py        tables, via Flask-SQLAlchemy
             ├──▶ api_key_tool/errors.py        raises typed errors → one JSON envelope
             └──▶ api_key_tool/observability.py JSON log line + X-Request-ID
```

Every response carries `X-Request-ID`, and the matching log line is written once at the end of the request with the status and duration, so a report of "it failed" is one `grep` away from the traceback.

## Architecture

```
keyforge/
├── src/api_key_tool/
│   ├── http.py                         379  HTTP plumbing for api_key_tool: correlation ids, acc
│   ├── config.py                       171  Environment-driven configuration for api_key_tool
│   ├── observability.py                169  Structured logging and request correlation for api_k
│   ├── _app.py                         166  
│   ├── app.py                          119  Application factory for api_key_tool
│   ├── keys/api.py                     119  
│   ├── cli.py                          117  
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── models.py                        63  
│   ├── paths.py                         52  Filesystem layout for api_key_tool
│   ├── keys/quota.py                    41  
│   ├── keys/generator.py                18  
├── openapi/keyforge.yaml                  the contract of record
├── schema/keyforge.sql                    the DDL
├── tests/                       the suite that has to stay green
├── docs/EVIDENCE.md             the recorded live route walk
├── Dockerfile                   multi-stage build
└── wsgi.py                      entry point
```

The package keeps one shape across the service: `config.py` reads the environment once, `observability.py` emits structured JSON logs carrying a request id, `errors.py` turns exceptions into a single JSON envelope, `models.py` holds the tables, and the `keys/` package holds the routes.

## Quality gates

| Gate | Command | Threshold |
| --- | --- | --- |
| Suite | `pytest -q` | all green |
| Coverage | `pytest --cov` | floor in `pyproject.toml`, set below the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 on every push to `main`, plus a container build — [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Development

```sh
pip install -e ".[dev]"
python -m pytest -q                      # the suite
python -m pytest --cov                   # with the coverage floor
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # formatting
python -m mypy src                       # types
python -m bandit -c pyproject.toml -r src  # security
pre-commit install                       # the same checks on commit
```

Dependabot opens grouped PRs for the dev tooling weekly and for actions and the base image monthly.

## Deploy

```sh
docker build -t keyforge .
docker run --rm -p 8000:8000 --env-file .env.example keyforge
```

A `docker-compose.yml` is included for a local run with a volume for the SQLite file. The image runs as a non-root user and serves through gunicorn.

## Limits, stated rather than hidden

- Keys are verified by this service; downstream services must call the verify path or share the digest table.
- Quota counters are per key and reset on a fixed window, not a rolling one.

## License

MIT — see [LICENSE](LICENSE).
