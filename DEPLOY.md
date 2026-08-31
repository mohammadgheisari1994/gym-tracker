# Deploying gym-tracker (free)

Target: a **Render** free web service (the app) + a **Neon** free PostgreSQL
database. Both have permanent free tiers. The app sleeps after ~15 minutes of
inactivity, so the first request after a quiet spell takes ~50 seconds.

## 1. Create the database (Neon)

1. Sign up at <https://neon.tech> and create a project (any region).
2. Open **Dashboard → Connect**. Turn the **Connection pooling** toggle **off**
   and copy the connection string. It looks like:

   ```
   postgresql://<user>:<password>@ep-xxxx.<region>.aws.neon.tech/<db>?sslmode=require
   ```

   The app rewrites `postgresql://` to the psycopg driver automatically and
   honours `sslmode=require`, so paste it exactly as Neon gives it.

## 2. Create the web service (Render)

1. Sign up at <https://render.com> and connect your GitHub account.
2. **New → Blueprint**, choose the `gym-tracker` repository. Render reads
   `render.yaml`.
3. Render will prompt for the secrets marked `sync: false`:
   - **`DATABASE_URL`** — the Neon string from step 1.
   - **`LLM_API_KEY`**, **`LLM_BASE_URL`** — leave blank for now.
4. `SECRET_KEY` is generated automatically; the rest have defaults.
5. Apply. The first deploy builds the Docker image, runs `alembic upgrade head`
   against Neon, then starts the app. Watch the logs until the health check at
   `/healthz` passes.

Your app is at `https://gym-tracker-<hash>.onrender.com`.

## 3. (Optional) Turn on the AI features

In the Render service's **Environment** tab, set one of:

| Provider | Variables |
| --- | --- |
| Groq (free, fast) | `LLM_PROVIDER=groq`, `LLM_API_KEY=<groq key>` |
| OpenRouter free models | `LLM_PROVIDER=openai`, `LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_API_KEY=<key>`, `LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free` |
| Cerebras | `LLM_PROVIDER=openai`, `LLM_BASE_URL=https://api.cerebras.ai/v1`, `LLM_API_KEY=<key>`, `LLM_MODEL=llama-3.3-70b` |

Save — Render redeploys. With `LLM_PROVIDER=none` the app never calls out and
the AI sections show a plain "unavailable" notice.

## Updating

Push to `main`. Render auto-deploys; `alembic upgrade head` runs on every boot,
so new migrations apply automatically.

## Notes

- Render terminates TLS at its edge, so `SESSION_HTTPS_ONLY=true` is correct —
  the session cookie is sent only over HTTPS.
- Neon's compute also autosuspends when idle; the first query after a pause
  adds ~0.5 s.
- Render's free database was deliberately *not* used: it is deleted after 30
  days. Neon's free tier does not expire.
