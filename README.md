# gym-tracker

A self-hostable workout tracker with progress analytics, estimated 1RM, a rest
timer, automated exercise form guides, and instructional videos.

Built with **FastAPI + HTMX + Jinja2**, backed by **PostgreSQL**, deployed on
**Render**. English-first UI with a Persian (Farsi) RTL option.

> Status: early development. See the
> [milestones](https://github.com/mohammadgheisari1994/gym-tracker/milestones)
> for the roadmap.

## Features (planned)

- Secure per-user accounts with fully isolated data.
- Dynamic exercise, set, weight, and rep management with reordering.
- Set tagging: normal, drop set, super set, warm-up, failure.
- Per-exercise progress charts (weight / volume / reps over time).
- Overall analytics: volume load, workout frequency, muscle-group distribution.
- Estimated 1RM (Epley) plotted on progress charts.
- Adjustable rest timer between sets.
- CSV / JSON export of workout history.
- Optional instructional video fetched per exercise.
- Automated, cached exercise form guides and performance insights via free LLM
  providers (no manual prompting).

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

## Project layout

```
app/
  main.py          FastAPI application factory
  config.py        Settings loaded from the environment
  database.py      SQLAlchemy engine and session
  models/          ORM models
  security/        Password hashing
  services/        Use-case logic (auth, and later workout tracking)
  web/             Routes, templates, forms, static assets
  i18n/            Translation catalogues (en, fa)
migrations/        Alembic migrations
tests/             Pytest suite
```

## What works today

Accounts (sign up, log in, profile, password change) with argon2-hashed
passwords and signed-cookie sessions. Every future feature scopes its data to
the signed-in user. Workout tracking is next.

## Contributing

See [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) and
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
