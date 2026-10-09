# LiteLLM gateway

A local, Docker Compose-based AI gateway with PostgreSQL for model management,
virtual keys and request records. Add API-key models or supported subscription
providers behind a shared API. The default configuration has no model routes.

## Repository layout

| File | Purpose |
| --- | --- |
| `docker-compose.quickstart.yml` | Gateway, database, localhost binding and persistent volumes |
| `config.yaml` | Model routes and gateway settings, mounted read-only |
| `.env.example` | Required credential names and optional settings |
| `scripts/init-env.py` | Create private local credentials; preserve an existing `.env` |
| `LiteLLM.postman_collection.json` | Model listing, completion and readiness requests |
| `skills/litellm-setup/SKILL.md` | Reusable setup workflow for agents |

## Set up on a new machine

Requires Git, Docker Engine with Compose v2 or later, and Python 3. Use Linux
containers; the pinned LiteLLM 1.104.0 image supports AMD64 and ARM64. Run commands
from the repository root. Credentials and data volumes are local to each machine.

```bash
python3 scripts/init-env.py
docker compose -f docker-compose.quickstart.yml config --quiet
docker compose -f docker-compose.quickstart.yml up -d
```

The initializer creates `.env` with random master, salt and database credentials
and mode `0600`. It never prints values or overwrites an existing file. Optional
settings from `.env.example` can be added locally. Use URL-safe database passwords,
or URL-encode them in `DATABASE_URL` if choosing your own.

The API is at `http://localhost:4000`; the dashboard is at
`http://localhost:4000/ui/`. PostgreSQL has no published port. The gateway binds
to `127.0.0.1` by default. Changing `LITELLM_BIND` to expose it requires separate
network access controls and TLS.

For the first dashboard login, use `admin` and the master key from your private
`.env`. Create a database-backed `proxy_admin` account, sign out and verify a fresh
login with that account. Then set `disable_env_credential_login: true` in
`config.yaml` and recreate the gateway using the command under Operations.
See the [dashboard setup guide](https://docs.litellm.ai/docs/proxy/ui).

## Add models

For reproducible routes, edit `config.yaml`. Models added through the dashboard
are stored in PostgreSQL and must be recreated or migrated on another machine.

### API-key model

Add `PROVIDER_API_KEY` to your private `.env`, then replace `model_list: []` with:

```yaml
model_list:
  - model_name: example-model
    litellm_params:
      model: <provider>/<model-id>
      api_key: os.environ/PROVIDER_API_KEY
```

Replace `<provider>/<model-id>` with the exact LiteLLM route for your chosen
provider and model. `model_name` is the client-facing alias; `litellm_params.model`
is the upstream route. Add `api_base` or other settings only when that provider
requires them. See [model configuration](https://docs.litellm.ai/docs/proxy/configs)
and [supported providers](https://docs.litellm.ai/docs/providers).

Compose explicitly passes `PROVIDER_API_KEY` into the gateway. If you add separate
credential variables for more providers, pass each through the service's
`environment` section too: placing a variable in `.env` alone does not inject it
into the container. Keep values out of YAML, collection exports and Git.

### Subscription provider: ChatGPT

LiteLLM supports ChatGPT through its built-in `chatgpt/` adapter and OAuth device
authorization. Access depends on the account, supported model and upstream limits.
Follow the [ChatGPT provider guide](https://docs.litellm.ai/docs/providers/chatgpt).

After creating `.env`, authorize in a one-off container **before adding the route**:

```bash
docker compose -f docker-compose.quickstart.yml run --rm --no-deps -T \
  --entrypoint python litellm -u - <<'PY_LOGIN'
import os
os.umask(0o077)
from litellm.llms.chatgpt.authenticator import Authenticator
auth = Authenticator()
os.chmod(auth.token_dir, 0o700)
auth.get_access_token()
os.chmod(auth.auth_file, 0o600)
print("Authorization saved to the local OAuth volume.")
PY_LOGIN
```

Open the printed verification URL and complete authorization yourself. The
temporary container shares the gateway's writable `chatgpt_tokens` volume; token
refresh requires that volume to remain writable. No login script or token file
belongs in the repository.

Add this entry to `model_list`, replacing `<model-id>` with a model your account
can access:

```yaml
  - model_name: chatgpt/<model-id>
    litellm_params:
      model: chatgpt/<model-id>
    model_info:
      mode: responses
      litellm_provider: chatgpt
```

Recreate the gateway after adding the route. Use the full configured name and
`stream: true` for this pinned setup. A listed route does not establish account
access; verify a completion. Repeat authorization if a refresh fails.

## Verify with Postman

Import `LiteLLM.postman_collection.json`. In Postman Local Vault, store a gateway
key as `litellm-api-key`; authorization references `{{vault:litellm-api-key}}`.
Local Vault is specific to the app and machine. Postman Web needs its own secret
and a compatible Desktop Agent to reach localhost.

Set `litellm_base_url`, `litellm_model` and `litellm_stream` in collection variables.
The default model alias is `example-model`; select your configured alias if
different. API-key providers may support JSON responses with `false`; use `true`
for the ChatGPT example.

1. Run **Gateway Readiness** and confirm a healthy gateway with a connected database.
2. Run **List Models** after adding a route and confirm its exact ID.
3. Run **Chat Completion - Gateway Test** and confirm its JSON or SSE assertions pass.

Use a model-scoped virtual key for routine clients. Reserve the master key for
administration. Readiness and model listing alone do not verify upstream inference.

## Operations and local state

```bash
# Validate without starting services or printing resolved credentials.
docker compose -f docker-compose.quickstart.yml config --quiet

# Apply configuration or environment changes to the gateway only.
docker compose -f docker-compose.quickstart.yml up -d --no-deps --force-recreate litellm

# Inspect recent gateway logs.
docker compose -f docker-compose.quickstart.yml logs --tail=100 litellm

# Remove containers and network; preserve data.
docker compose -f docker-compose.quickstart.yml down
```

`postgres_data` holds database accounts, keys, routes and logs. `chatgpt_tokens`
holds OAuth credentials. Preserve `.env`, especially `LITELLM_SALT_KEY`, while
reusing database data: changing the salt makes stored provider credentials
unreadable. Keep the Compose project name stable to reuse the same volumes.
`LITELLM_IMAGE` can override the pinned image for a deliberate upgrade.

For an intentional full reset, `docker compose -f docker-compose.quickstart.yml
down --volumes` permanently deletes both volumes. Remove `.env` only when also
discarding that database. A new machine gets fresh state without deleting anything
on the original machine. `.gitignore` excludes local credentials and runtime files.

## Agent-assisted setup

Ask an agent to read [the setup skill](skills/litellm-setup/SKILL.md) and set up
this checkout with your chosen provider and model. It is plain Markdown with
standard skill metadata, so agents can read it directly or install it in their
own skill directory. The skill distinguishes preparing files from starting
services and verifies readiness, routing and inference separately.
