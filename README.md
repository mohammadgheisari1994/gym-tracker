# gym-tracker

A self-hostable workout tracker with progress analytics, estimated 1RM, a rest
timer, automated exercise form guides, and instructional videos.

Built with **FastAPI + HTMX + Jinja2**, backed by **PostgreSQL**, deployed on
**Render**. English-first UI with a Persian (Farsi) RTL option.

## Features

- **Accounts** — sign up / log in / profile, argon2-hashed passwords,
  signed-cookie sessions. Every query is scoped to the signed-in user.
- **Exercise catalogue** — your own list of movements, each with a muscle
  group and notes.
- **Workout logging** — sessions of exercises and sets (weight, reps, RPE),
  set tags (normal / warm-up / drop / super / failure) with colour badges,
  reorder exercises and sets, add-set form pre-filled from your last set.
- **Analytics** — dashboard charts for weekly volume load, workout frequency,
  and muscle-group distribution; per-exercise progress charts for top weight,
  volume, reps, and estimated 1RM.
- **Estimated 1RM** — Epley formula, plotted alongside top weight.
- **Rest timer** — floating countdown on the workout page, adjustable, with a
  tone at zero; per-user default duration.
- **Data export** — full workout history as CSV (one row per set) or JSON.
- **LLM features** (opt-in, off by default) — a cached execution guide per
  exercise, a textual performance-insight summary, and a daily motivational
  line. Prompts are built from your own data; the user never types one.
- **Instructional videos** — embedded from YouTube (primarily Jeff Nippard),
  auto-matched for common lifts, never downloaded.
- **Internationalised** — English and Persian (RTL) throughout.

## Local development

Requirements: Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

The app is served at http://localhost:8000.

Run the checks:

```bash
docker compose run --rm app ruff check .
docker compose run --rm app pytest
```

## Enabling the LLM features

Set an LLM provider in the environment (see `.env.example`). Free options:

| Provider | Config |
| --- | --- |
| Groq | `LLM_PROVIDER=groq`, `LLM_API_KEY=...` |
| Any OpenAI-compatible endpoint (OpenRouter, Cerebras, Gemini) | `LLM_PROVIDER=openai`, `LLM_BASE_URL=...`, `LLM_API_KEY=...`, `LLM_MODEL=...` |
| Self-hosted Ollama | `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://host:11434` |

With `LLM_PROVIDER=none` (the default) the app makes no external calls and the
LLM sections show a plain "unavailable" notice.

## Deployment

`render.yaml` is a Render Blueprint for a free web service, backed by an
external free [Neon](https://neon.tech) PostgreSQL database. See
[DEPLOY.md](DEPLOY.md) for the step-by-step.

## Project layout

```
app/
  main.py            FastAPI application factory
  config.py          Settings loaded from the environment
  database.py        SQLAlchemy engine and session
  models/            ORM models
  security/          Password hashing
  services/          Use-case logic (one module per feature)
  llm/               LLM provider abstraction
  references/        Curated, verified citation catalogue
  exercise_videos/   Curated exercise -> video seed
  web/               Routes, templates, forms, static assets
  i18n/              Translation catalogues (en, fa)
migrations/          Alembic migrations
tests/               Pytest suite
```

## Contributing

See [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) and
[CONTRIBUTING.md](CONTRIBUTING.md).

## References & attributions

Training guidance is grounded in cited, peer-reviewed research (see
[`/references`](app/references/catalog.py) in-app; every DOI verified against
Crossref). Instructional videos are embedded from YouTube — primarily
[Jeff Nippard](https://www.youtube.com/@JeffNippard) — and never downloaded.
LLM-generated text is original, carries an "educational, not coaching or medical
advice" disclaimer, and links the catalogue works as further reading. Full
third-party attributions are in [NOTICE](NOTICE).

## License

[MIT](LICENSE)
