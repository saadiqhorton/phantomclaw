---
description: How to start the persistent external Telegram chat agent using OpenCode and Minimax
---
# External Chat using Telegram & OpenCode (Minimax)

This workflow starts a persistent Telegram bot that pipes your phone's multimodal input directly into your local `opencode` session utilizing your Minimax subscription. This gives you persistent open code access to your workspace from anywhere.

## Prerequisites
1. Telegram Bot Token (Get one from @BotFather on Telegram).
2. Minimax API Key (Your coding plan subscription).
3. Python packages: `python-telegram-bot`
4. The OpenCode CLI installed globally (`npm install -g @googleworkspace/cli` / `opencode`)

## Setup
1. Add the following to your projects `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   MINIMAX_API_KEY=your_minimax_key
   # MINIMAX_MODEL is optional, defaults to minimax-coding-plan/MiniMax-M2.5
   # TELEGRAM_ALLOWED_USER_ID is optional but highly recommended to prevent others from using your bot
   TELEGRAM_ALLOWED_USER_ID=your_numeric_telegram_id
   ```
2. Install the required python library:
   ```bash
   pip install python-telegram-bot
   ```

## Execution
Run the bridge script from your terminal:
```bash
python tools/telegram_opencode_bridge.py
```

## Usage
Simply send text, images, voice notes, or files to your Telegram bot. 

The bridge script will:
1. Download the rich media locally to your `/tmp/` directory.
2. Format it into an intelligent prompt.
3. Automatically execute `opencode run -s mobile_session --model minimax/model "prompt"` on your local machine, picking up exactly where you left off.
4. Stream the terminal standard output back to your chat.
