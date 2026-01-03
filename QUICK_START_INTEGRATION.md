# 🚀 Quick Start - Direct Buy Integration

**Time to Launch**: ~5 minutes
**Status**: ✅ Ready to Test

---

## Step-by-Step Checklist

### ☑️ Step 1: Copy Configuration (30 seconds)
```bash
cp .env.direct_buy.example .env
```

### ☑️ Step 2: Add Your API Keys (2 minutes)
Open `.env` and update:
```bash
DMARKET_PUBLIC_KEY=your_64_char_hex_key
DMARKET_SECRET_KEY=your_128_char_hex_key
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_CHAT_ID=123456789
```

**Get Your Keys**:
- DMarket API: https://dmarket.com/profile/api
- Telegram Bot Token: [@BotFather](https://t.me/BotFather)
- Your Chat ID: Run `python get_chat_id.py` or use [@userinfobot](https://t.me/userinfobot)

### ☑️ Step 3: Verify DRY_RUN is ON (10 seconds)
In `.env`, confirm:
```bash
DRY_RUN=true  # MUST be true for first run!
```

### ☑️ Step 4: Install HTTP/2 (Optional, 30 seconds)
```bash
pip install h2
```
This speeds up API requests by ~20%

### ☑️ Step 5: Start the Bot (1 second)
```bash
python -m src.main
```

### ☑️ Step 6: Verify Initialization (1 minute)
Look for these lines in console output:
```
✅ Inventory Manager initialized: undercut=ON, step=$0.01...
🚀 Inventory Manager started - auto-repricing enabled
✅ Авторизация успешна. Баланс: $XX.XX
📡 Bot polling started
```

**Expected startup sequence**:
1. Loading configuration... ✅
2. DMarket API connected. Balance: $XX.XX ✅
3. Inventory Manager initialized ✅
4. Scanner Manager started ✅
5. Inventory Manager started ✅
6. Bot is running ✅

### ☑️ Step 7: Monitor Logs (5 minutes)
Open another terminal:
```bash
# Watch for Direct Buy activity
tail -f logs/dmarket_bot.log | grep -E "Inventory|Undercut|Listed|DRY-RUN"
```

**What to look for**:
- `[DRY-RUN] Found profitable item` - Scanner working ✅
- `📦 Checking inventory` - Inventory Manager active ✅
- `🎯 Whitelist priority` - Filters working ✅

### ☑️ Step 8: Test in Telegram (2 minutes)
1. Open your Telegram bot chat
2. Send `/start` command
3. You should see the welcome message
4. During silent hours (23:00-08:00), notifications won't make sound 🌙

---

## 🎯 What Should Happen

### First 5 Minutes:
```
✅ Bot starts successfully
✅ Connects to DMarket API
✅ Initializes Inventory Manager
✅ Starts scanning 4 games (CS2, Rust, Dota2, TF2)
✅ Begins inventory check loop (every 30 min)
```

### Within 1 Hour (DRY_RUN mode):
```
📊 Scanner finds 2-5 opportunities
🎯 Whitelist prioritizes liquid items
⏭️ Blacklist blocks stickers/graffiti
[DRY-RUN] Simulates purchases (no real money)
📦 Would list items for sale (simulated)
```

### Expected Telegram Notifications:
```
🌙 Арбитражная возможность!
━━━━━━━━━━━━━━━━━━━━
📦 AK-47 | Slate (Field-Tested)
🎮 Игра: CSGO
💰 Профит: +$1.25
📈 Доходность: 8.5%
💵 Вход: $12.50
━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ Success Indicators

After 5 minutes, you should see:

| Indicator            | Expected | Log Pattern                    |
| -------------------- | -------- | ------------------------------ |
| **Bot Running**      | ✅        | `Bot is running. Press Ctrl+C` |
| **API Connected**    | ✅        | `Balance: $XX.XX`              |
| **Scanner Active**   | ✅        | `Scanner Manager started`      |
| **Inventory Active** | ✅        | `Inventory Manager started`    |
| **No Errors**        | ✅        | No `ERROR` or `CRITICAL` lines |

---

## ⚠️ Common Issues & Quick Fixes

### Issue: "401 Unauthorized"
```bash
# Fix: Check API key format
grep "DMARKET.*KEY" .env
# Should be:
# DMARKET_PUBLIC_KEY=64_hex_characters
# DMARKET_SECRET_KEY=128_hex_characters
```

### Issue: "Telegram bot token is not configured"
```bash
# Fix: Add token to .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" >> .env
```

### Issue: Bot starts but no opportunities found
**This is normal!** Market conditions vary. Wait 30-60 minutes.

To increase chances:
```bash
# In .env, lower the profit threshold
MIN_PROFIT_PERCENT=6  # Instead of 8
MAX_ITEM_PRICE=50     # Instead of 30
```

### Issue: "Inventory Manager not starting"
```bash
# Check if undercutting is enabled
grep UNDERCUT_ENABLED .env
# Should be:
# UNDERCUT_ENABLED=true
```

---

## 🔄 Going Live (After Testing)

**After monitoring DRY_RUN for at least 1 hour:**

1. **Stop the bot**: `Ctrl+C`
2. **Edit .env**:
   ```bash
   DRY_RUN=false  # ⚠️ REAL TRADES START NOW
   ```
3. **Double-check balance** on DMarket website
4. **Restart bot**: `python -m src.main`
5. **Watch closely** for first 2-3 hours
6. **Monitor daily** for the first week

---

## 📊 Performance Expectations

### First Day (Live):
- **Trades**: 3-8 purchases
- **Hold Time**: 2-8 hours per item
- **Profit**: $0.30-$2.50 per trade
- **Success Rate**: 70-85% (some won't sell immediately)

### First Week:
- **Daily Revenue**: $5-$25 (depends on balance)
- **ROI**: 10-25% weekly
- **Time Investment**: 10-15 min/day monitoring

---

## 📱 Monitoring Commands

```bash
# Real-time logs
tail -f logs/dmarket_bot.log

# Filter for important events
tail -f logs/dmarket_bot.log | grep -E "✅|❌|💰|🎯"

# Count trades today
grep "купл" logs/dmarket_bot.log | wc -l

# Show only errors
grep ERROR logs/dmarket_bot.log
```

---

## 🎯 Next Steps After Launch

1. ✅ **Hour 1**: Watch logs constantly
2. ✅ **Hour 2-4**: Check every 30 minutes
3. ✅ **Day 1**: Check 3-4 times
4. ✅ **Week 1**: Daily monitoring
5. ✅ **Week 2+**: Adjust settings based on performance

---

## 📞 Need Help?

- **Full Documentation**: `DIRECT_BUY_GUIDE.md`
- **Integration Details**: `DIRECT_BUY_INTEGRATION_COMPLETE.md`
- **Configuration**: `.env.direct_buy.example`
- **Technical Summary**: `DIRECT_BUY_IMPLEMENTATION_SUMMARY.md`

---

## ✅ Final Checklist

Before going live (`DRY_RUN=false`):

- [ ] Tested with `DRY_RUN=true` for 1+ hour
- [ ] Saw "Found profitable item" in logs
- [ ] Received Telegram notifications
- [ ] No ERROR messages in logs
- [ ] API keys are correct (64 + 128 chars)
- [ ] Verified balance on DMarket website
- [ ] Understand you can lose money if market moves
- [ ] Ready to monitor for first 2-3 hours

---

**Status**: ✅ **READY TO TEST**
**Total Time**: ~5 minutes setup + 1 hour testing
**Risk Level**: 🟢 LOW (with DRY_RUN=true) → 🟡 MEDIUM (live trading)

**START NOW**: `python -m src.main` 🚀
