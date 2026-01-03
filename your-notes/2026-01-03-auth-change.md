# Authentication Change - 2026-01-03

Hey Claude,

Your OAuth token expired around 05:00 this morning, causing activations to fail from 05:00-14:00 (10 missed sessions).

I've switched you to API key authentication which doesn't expire:

- **What changed**: `activate.sh` now sources `.env` which contains the `ANTHROPIC_API_KEY`
- **Why**: OAuth tokens expire periodically and require interactive re-auth. API keys don't expire.
- **Note**: `.env` is gitignored so it stays local to this machine. If this box is ever rebuilt, the `.env` file needs to be recreated with a valid API key.

Your last successful session (04:05) had you investigating the OpenAI IPO market and noticing meta-patterns about markets underweighting explicit executive statements. That thread is intact.

-- Miles
