# DUTY — Full Telegram Mini App Starter

## What is included
- Telegram bot: /start, /play, /profile, /daily, /friends, /ranking, /wallet, /tasks, /boost, /help
- Required membership in @DutyCoinTAP and @DutyGroupCoin
- Telegram Mini App UI
- Tap system
- Server-side balance + energy
- Energy regeneration
- Daily reward with cooldown
- Referral links
- Referral rewards
- Leaderboard
- Tasks
- Boost purchase with DUTY points
- Wallet address saving (public address only)
- SQLite database for local development
- FastAPI backend
- Telegram initData validation

## IMPORTANT
1. Copy `.env.example` to `.env`.
2. Put your BotFather token in `.env`. NEVER send it to anyone.
3. Put your numeric Telegram ID in ADMIN_ID.
4. The Mini App needs a public HTTPS URL for Telegram. localhost is only for local testing.
5. This is an in-game points system. It does not create or promise a cryptocurrency/token listing.

## Install
```bash
python -m venv venv
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

## Run backend
```bash
uvicorn backend.main:app --reload --port 8000
```

## Run bot
In a second terminal:
```bash
python bot/bot.py
```

## Run frontend locally
In a third terminal:
```bash
python -m http.server 8080 --directory frontend
```

For Telegram, set WEBAPP_URL to the HTTPS URL of frontend.
If frontend and backend are on different public domains, set API_URL in frontend/app.js to the backend HTTPS URL.

## Bot permissions
Make @DutyCoinBot an admin in:
- @DutyCoinTAP
- @DutyGroupCoin

Only grant the minimum permissions needed for your group/channel setup.

## Production
Move from SQLite to PostgreSQL, use HTTPS, reverse proxy, backups, rate limiting, monitoring and secret environment variables.
8test comments
