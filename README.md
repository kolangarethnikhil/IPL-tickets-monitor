# 🏏 IPL Ticket Alert Bot

A Python bot that monitors **BookMyShow** for IPL ticket availability and sends you **instant Telegram alerts** the moment tickets open up — running 24/7 in the cloud, even when your laptop is off.

---

## ✨ Features

- 🔍 **Monitors BookMyShow** for IPL match tickets in your city
- 📲 **Instant Telegram alerts** when tickets become available or are filling fast
- 💓 **Heartbeat messages** every hour so you know the bot is alive
- 🔁 **Deduplication** — won't spam you with the same alert repeatedly
- ☁️ **Cloud deployable** on Railway or Render (free tiers available)
- ⚙️ **Fully configurable** via environment variables

---

## 🚀 Quick Start (Local)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/ipl-ticket-alert.git
cd ipl-ticket-alert
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your Telegram Bot

**Step A — Create a bot:**
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** (looks like `123456789:ABCdef...`)

**Step B — Get your Chat ID:**
1. Search for **@userinfobot** on Telegram
2. Send `/start` — it replies with your Chat ID

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and fill in your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

### 5. Run the bot
```bash
python main.py
```

You'll get a Telegram message confirming the bot has started, along with a status summary of upcoming IPL matches.

---

## ☁️ Deploy to Railway (Runs 24/7, Free)

**Railway** gives you $5 free credits/month — more than enough for this lightweight bot.

### Steps:

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ipl-ticket-alert.git
   git push -u origin main
   ```

2. **Go to [railway.app](https://railway.app)** → Sign in with GitHub

3. **New Project → Deploy from GitHub Repo** → Select your repo

4. **Add environment variables** in Railway dashboard:
   - Go to your service → **Variables** tab
   - Add `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CITY`, etc.
   - ⚠️ Do NOT commit your `.env` file — set vars directly in Railway

5. **Deploy** — Railway auto-detects `railway.toml` and runs `python main.py`

That's it! The bot now runs 24/7 in the cloud. ✅

---

## ☁️ Deploy to Render (Alternative)

1. Go to [render.com](https://render.com) → New → **Background Worker**
2. Connect your GitHub repo
3. Set **Build Command:** `pip install -r requirements.txt`
4. Set **Start Command:** `python main.py`
5. Add your environment variables under **Environment**
6. Click **Create Background Worker**

---

## ⚙️ Configuration

All config is via environment variables (set in `.env` locally, or in Railway/Render dashboard):

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | *required* | Your bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | *required* | Your personal chat ID from @userinfobot |
| `CITY` | `bangalore` | City to monitor tickets for |
| `CHECK_INTERVAL_SECONDS` | `120` | How often to check (in seconds) |
| `HEARTBEAT_EVERY_N_CHECKS` | `30` | Send alive-ping every N checks |
| `ALERT_COOLDOWN_SECONDS` | `3600` | Re-alert cooldown per match |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Supported Cities
`bangalore`, `mumbai`, `delhi`, `chennai`, `kolkata`, `hyderabad`, `pune`, `ahmedabad`, `jaipur`, `lucknow`

---

## 📁 Project Structure

```
ipl-ticket-alert/
├── main.py               # Entry point — the main alert loop
├── src/
│   ├── scraper.py        # BookMyShow scraper
│   ├── telegram_bot.py   # Telegram notification helpers
│   └── config.py         # Config loader from env vars
├── requirements.txt
├── railway.toml          # Railway deployment config
├── Procfile              # Render deployment config
├── .env.example          # Template for environment variables
├── .gitignore
└── README.md
```

---

## ⚠️ Notes

- BookMyShow's internal API structure may change — if the bot stops finding matches, check the scraper and update the API endpoint/params.
- This bot is for personal use. Excessive automated requests may violate BookMyShow's Terms of Service.
- Set `CHECK_INTERVAL_SECONDS` to at least `60` to be respectful of their servers.

---

## 🤝 Contributing

PRs welcome! Ideas for improvements:
- [ ] Support for multiple cities simultaneously  
- [ ] Support for Paytm Insider / team-specific sites
- [ ] WhatsApp notifications via Twilio
- [ ] Web dashboard showing match status

---

## 📄 License

MIT
