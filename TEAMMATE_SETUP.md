# Teammate Setup

Use this guide to get the project running locally without guessing which env values to use.

## Project Link

`https://github.com/ssamadjon3106/Hackathon.git`

## Clone The Repo

```bash
git clone https://github.com/ssamadjon3106/Hackathon.git
cd Hackathon
```

## Create Local Env File

```bash
cp .env.example .env
```

Edit `.env` and choose one provider setup below.

## Option 1: Basic Local Run Without Paid AI

This uses the fallback internal generation path.

```env
LLM_PROVIDER=vertex
EMBEDDING_PROVIDER=deterministic
GEMINI_PROJECT_ID=
OPENAI_API_KEY=
```

## Option 2: OpenRouter

```env
LLM_PROVIDER=openrouter
OPENAI_API_KEY=their_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1
EMBEDDING_PROVIDER=deterministic
GEMINI_PROJECT_ID=
```

## Option 3: Google Cloud / Gemini

```env
LLM_PROVIDER=vertex
GEMINI_PROJECT_ID=their_gcp_project_id
GEMINI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
EMBEDDING_PROVIDER=deterministic
OPENAI_API_KEY=
```

## Set Admin Bootstrap Values

Add these to `.env`:

```env
BOOTSTRAP_ADMIN_EMAIL=their_email@example.com
BOOTSTRAP_ADMIN_PASSWORD=their_strong_password
BOOTSTRAP_ADMIN_TOKEN=some_random_secret
```

## Start The Stack

```bash
docker compose up --build
```

## Check Auth Service

```bash
curl http://localhost:8001/health
```

## Bootstrap Admin

```bash
curl -X POST http://localhost:8001/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "their_email@example.com",
    "full_name": "Their Name",
    "password": "their_strong_password",
    "bootstrap_token": "some_random_secret"
  }'
```

## Log In

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "their_email@example.com",
    "password": "their_strong_password"
  }'
```

## Open API Docs

`http://localhost:8000/docs`

## Important

- Do not commit `.env`.
- Do not share API keys in GitHub.
- If you pasted any real key earlier, rotate it before sharing.

## Recommended Notes For Teammates

- If they just want to test the app, use fallback mode with no paid AI key.
- If they want real AI generation, use either OpenRouter or Gemini, not both at the same time.
