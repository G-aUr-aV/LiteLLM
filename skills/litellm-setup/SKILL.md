---
name: litellm-setup
description: Set up this repository's Docker Compose LiteLLM gateway on a new machine, add API-key or supported subscription models, and verify the resulting service. Use for fresh setup or model configuration in this checkout.
---

# LiteLLM setup

Use the repository's maintained Compose file and config. Locate its root from
the user's checkout; relative to this skill it is `../..`. Read `README.md`,
`.env.example`, `config.yaml`, `docker-compose.quickstart.yml`, and
`scripts/init-env.py` before making changes. Do not download an upstream
quickstart over these files or assume previously configured database routes exist.

## Scope and prerequisites

- Respect the requested phase. For cleanup or preparation only, edit and validate
  files without pulling images, authorizing accounts or starting services.
- For installation, check Docker, Compose v2 or later, Python 3 and port 4000
  (or the configured port). The pinned gateway image supports AMD64 and ARM64.
- Resolve the chosen provider and exact model ID from the request or existing
  configuration. If missing, ask before registering a route. Consult the provider's
  current LiteLLM documentation for its credentials and endpoint requirements.
- Keep existing keys, volumes, unrelated routes and application settings intact
  unless their removal is authorized. A full reset requires explicit permission
  to delete database data and OAuth credentials; container removal retains them.

## Credentials and routes

Run `python3 scripts/init-env.py` for a new `.env`; it preserves an existing file
and generates URL-safe credentials with owner-only permissions. Never display
credential values or resolved Compose output; use `config --quiet`. Preserve the
salt while retaining database data. Keep secrets in local `.env`, a secret manager
or the target app, and never ask for them in chat.

For an API-key provider, configure an explicit `model_name` alias and
`litellm_params.model: <provider>/<model-id>`. Reference the credential using
`os.environ/PROVIDER_API_KEY`, or a distinct variable when needed. Pass that
variable through the gateway's Compose `environment`; `.env` interpolation alone
does not inject it. Set `api_base` only when required. Do not silently drop
unsupported request parameters for every provider.

For ChatGPT, use the README's isolated one-off container to complete device
authorization before enabling a `chatgpt/` route. The owner performs the browser
authorization. Both containers must share the writable OAuth volume. Register
an explicit namespaced model with `model_info.mode: responses` and use streaming
for the pinned setup. Do not copy another application's OAuth file or add token
files to Git. Other subscriptions require their own supported adapter and flow.

File-defined routes are reproducible; dashboard-defined routes live in PostgreSQL.
Do not treat listing a model as proof of provider access or account entitlement.

## Start and verify

Run from the repository root:

```bash
docker compose -f docker-compose.quickstart.yml config --quiet
docker compose -f docker-compose.quickstart.yml up -d
```

On a fresh database, bootstrap the dashboard as documented. Create a database
`proxy_admin`, verify a fresh password login, then enable
`disable_env_credential_login: true` and recreate only the gateway. Enabling that
restriction before establishing an admin locks out first-time dashboard login.
Leave an existing installation's chosen login restriction intact.

Verify these outcomes separately, using secrets without echoing them:

1. `/health/readiness` reports healthy and the database connected.
2. Authenticated `/v1/models` includes the chosen client-facing model ID.
3. One small completion for the selected route returns an assistant response;
   streaming must finish without error events. This request uses provider quota.

Use the included Postman collection when the user requests Postman verification.
Its Vault reference must resolve in the target app and machine. Run the saved
requests; a configured header or CLI login is not a successful request.

For file or environment changes after startup:

```bash
docker compose -f docker-compose.quickstart.yml up -d --no-deps --force-recreate litellm
```

If startup or verification fails, inspect bounded logs and the provider's contract;
avoid repeated billable requests or logging secrets. Report the specific failed
layer and stop once credentials, entitlement or user authorization are required.
Finish with changed files, checks actually run, observed service state and any
remaining manual action. Never claim a fresh-machine installation passed after
only validating files. Do not commit or push unless asked.
