# 🏏 IPL Ticket Alert Bot — RCB Edition

Monitors **shop.royalchallengers.com/ticket** (RCB TicketGenie) + **BookMyShow** for IPL ticket availability and sends **instant Telegram alerts**. Runs 24/7 in the cloud even when your laptop is off.

---

## 🔴 Priority Watch: April 24 RCB Match

The bot gives special priority to the **April 24 home match**. You'll get:
- An immediate ping if tickets are already live when the bot starts
- A "still watching" notice if they haven't dropped yet
- A loud `🔥 PRIORITY MATCH ALERT` when they go live

---

## ✨ How it works

| Source | What it does |
|---|---|
| **RCB TicketGenie** (primary) | Hits the official `rcbmpapi.ticketgenie.in/ticket/eventlist/o` API that powers `shop.royalchallengers.com/ticket` |
| **BookMyShow** (fallback) | Scans BMS for any IPL matches in your city |

---

## 🚀 Quick Start (Local)

```bash
git clone https://github.com/YOUR_USERNAME/ipl-ticket-alert.git
cd ipl-ticket-alert
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
python main.py
```

---

## 📲 Telegram Setup (5 mins)

**Step 1 — Create your bot:**
1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → copy the **Bot Token**

**Step 2 — Get your Chat ID:**
1. Search **@userinfobot** on Telegram
2. Send `/start` → copy your **Chat ID**

**Step 3 — Add to .env:**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstUVwXyZ
TELEGRAM_CHAT_ID=987654321
```

---

## ☁️ Deploy to Railway (Runs 24/7 — Free)

> This is how it runs when your laptop is off.

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub Repo**
3. Select your repo
4. Go to **Variables** tab → add your env vars:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `CITY` = `bangalore`
   - `CHECK_INTERVAL_SECONDS` = `90`
5. Deploy — Railway auto-detects `railway.toml` and runs `python main.py` ✅

---

## ☁️ Deploy to Render (Alternative)

1. [render.com](https://render.com) → **New → Background Worker**
2. Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python main.py`
5. Add environment variables → **Create Background Worker** ✅

---

## ⚙️ Config Reference

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | required | From @BotFather |
| `TELEGRAM_CHAT_ID` | required | From @userinfobot |
| `CITY` | `bangalore` | For BMS fallback |
| `CHECK_INTERVAL_SECONDS` | `90` | Poll frequency |
| `HEARTBEAT_EVERY_N_CHECKS` | `40` | ~Every hour |
| `ALERT_COOLDOWN_SECONDS` | `3600` | Prevents duplicate alerts |
| `LOG_LEVEL` | `INFO` | Verbosity |

---

## 📁 Project Structure

```
ipl-ticket-alert/
├── main.py                  ← Main alert loop (RCB primary + BMS fallback)
├── src/
│   ├── rcb_scraper.py       ← RCB TicketGenie API (shop.royalchallengers.com)
│   ├── scraper.py           ← BookMyShow fallback scraper
│   ├── telegram_bot.py      ← Telegram message helpers
│   └── config.py            ← Env var config loader
├── requirements.txt
├── railway.toml             ← Railway auto-deploy config
├── Procfile                 ← Render config
├── .env.example
└── README.md
```

---

## ⚠️ Notes

- RCB TicketGenie API (`rcbmpapi.ticketgenie.in`) is an internal API — its structure may change between seasons
- Set `CHECK_INTERVAL_SECONDS` ≥ 60 to be respectful of their servers
- For personal use only

---

## 📄 License
MIT
