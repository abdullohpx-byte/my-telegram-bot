# README.md

## Abdulloh Telegram Bot

This repository contains a Telegram bot built with **aiogram** that provides a product catalog, price list, consultation mode, and help menu. All interactive buttons are rendered as **inline keyboards** attached to bot messages.

### Features
- Inline main menu with buttons: `Mahsulotlar`, `Narxlar`, `Maslahat olish`, `Yordam`.
- Product listing with dynamic inline buttons.
- Detailed product view with ordering capability.
- Consultation mode where users can ask questions.
- Clean UI: no persistent reply keyboard; all buttons appear under bot messages.

### Deployment
The bot can be deployed to **Render** using the provided `render.yaml`. Render will automatically install dependencies from `requirements.txt` and start the bot with `python bot.py`.

A cron job is configured to restart the bot at **1:05 AM** UTC (as requested) to ensure it stays fresh.

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

### License
MIT License (you can change as needed).
