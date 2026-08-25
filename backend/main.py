import json, os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, desc
from dotenv import load_dotenv
from .database import init_db, SessionLocal
from .models import User, Task
from .auth import validate_telegram_init_data

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
app = FastAPI(title="DUTY API")

# The Mini App (browser/webview) and this API are almost always served from two
# different origins (different domain in production, or e.g. localhost:8080 vs
# localhost:8000 in local dev). Without CORS enabled, every fetch() call from
# the frontend fails and looks like "server error" even though the backend is
# healthy. Every write endpoint below already requires a valid, Telegram-signed
# init_data, so a permissive origin list here does not weaken that check.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

class InitRequest(BaseModel):
    init_data: str

class TapRequest(BaseModel):
    init_data: str
    taps: int = 1

class WalletRequest(BaseModel):
    init_data: str
    wallet: str

def tg_user(init_data):
    data = validate_telegram_init_data(init_data, BOT_TOKEN)
    if not data or "user" not in data:
        raise HTTPException(401, "Invalid Telegram session")
    return json.loads(data["user"])

def regen(user):
    now = datetime.utcnow()
    elapsed = max(0, int((now - user.energy_updated_at).total_seconds()))
    # 1 energy per 3 seconds
    gained = elapsed // 3
    if gained:
        user.energy = min(user.max_energy, user.energy + gained)
        user.energy_updated_at = now

async def get_user(tg):
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            u = User(telegram_id=tg["id"], username=tg.get("username"), first_name=tg.get("first_name"))
            db.add(u)
            await db.commit()
            await db.refresh(u)
        return u

def payload(u):
    return {
        "telegram_id": u.telegram_id, "username": u.username, "first_name": u.first_name,
        "balance": u.balance, "energy": u.energy, "max_energy": u.max_energy,
        "level": u.level, "tap_power": u.tap_power, "wallet": u.wallet,
        "referral_count": u.referral_count
    }

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/api/user")
async def user(req: InitRequest):
    tg = tg_user(req.init_data)
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            u = User(telegram_id=tg["id"], username=tg.get("username"), first_name=tg.get("first_name"))
            db.add(u)
            await db.commit()
            await db.refresh(u)
        regen(u)
        await db.commit()
        return payload(u)

@app.post("/api/tap")
async def tap(req: TapRequest):
    if not 1 <= req.taps <= 50:
        raise HTTPException(400, "Invalid tap batch")
    tg = tg_user(req.init_data)
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            u = User(telegram_id=tg["id"], username=tg.get("username"), first_name=tg.get("first_name"))
            db.add(u)
            await db.flush()
        regen(u)
        allowed = min(req.taps, u.energy)
        earned = allowed * u.tap_power
        u.energy -= allowed
        u.balance += earned
        u.energy_updated_at = datetime.utcnow()
        await db.commit()
        return {"balance": u.balance, "energy": u.energy, "earned": earned}

@app.post("/api/daily")
async def daily(req: InitRequest):
    tg = tg_user(req.init_data)
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            raise HTTPException(404, "User not found")
        now = datetime.utcnow()
        if u.daily_claimed_at and now - u.daily_claimed_at < timedelta(hours=24):
            left = timedelta(hours=24) - (now - u.daily_claimed_at)
            return {"ok": False, "message": f"Come back in {left.seconds//3600}h {(left.seconds%3600)//60}m"}
        u.balance += 500
        u.daily_claimed_at = now
        await db.commit()
        return {"ok": True, "reward": 500, "balance": u.balance}

@app.get("/api/ranking")
async def ranking():
    async with SessionLocal() as db:
        r = await db.execute(select(User).order_by(desc(User.balance)).limit(20))
        return [{"username": u.username or u.first_name or "Soldier", "balance": u.balance} for u in r.scalars()]

@app.post("/api/wallet")
async def wallet(req: WalletRequest):
    tg = tg_user(req.init_data)
    wallet = req.wallet.strip()
    if len(wallet) < 10 or len(wallet) > 120:
        raise HTTPException(400, "Invalid wallet address format")
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            raise HTTPException(404, "User not found")
        u.wallet = wallet
        await db.commit()
        return {"ok": True, "wallet": wallet}

@app.get("/api/tasks")
async def tasks():
    async with SessionLocal() as db:
        r = await db.execute(select(Task).where(Task.active == True))
        items = list(r.scalars())
        if not items:
            # Starter tasks; these are definitions only.
            items = [
                Task(id=1, title="Join the DUTY community", reward=250, active=True),
                Task(id=2, title="Reach 1,000 DUTY", reward=500, active=True),
            ]
        return [{"id": t.id, "title": t.title, "reward": t.reward} for t in items]

@app.post("/api/boost")
async def boost(req: InitRequest):
    tg = tg_user(req.init_data)
    async with SessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == tg["id"]))
        u = r.scalar_one_or_none()
        if not u:
            raise HTTPException(404, "User not found")
        cost = 1000 * u.tap_power
        if u.balance < cost:
            raise HTTPException(400, f"Need {cost} DUTY")
        u.balance -= cost
        u.tap_power += 1
        await db.commit()
        return {"ok": True, "balance": u.balance, "tap_power": u.tap_power}
