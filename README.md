# Discord Coach Bot

A Python Discord bot that sends scheduled daily check-ins via DM and writes responses to Craft daily notes for automated habit tracking.

## Features

- **Morning Check-in (7:00 AM)**: Asks about morning routine completion
- **Evening Check-in (5:30 PM)**: Asks about exercise/workout completion
- **Craft Integration**: Automatically appends responses to your Craft daily notes
- **Single-user DM**: Designed for personal use with one specific Discord user

## Prerequisites

- Python 3.11 or higher
- Discord bot token (from Discord Developer Portal)
- Your Discord user ID
- Craft API access and URL
- Railway account (for deployment) or local environment

## Local Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd DiscordCoachBot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_USER_ID=your_discord_user_id_here
CRAFT_API_URL=your_craft_api_url_here
TIMEZONE=America/Denver
```

### 4. Getting Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Token", click "Reset Token" and copy it
6. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
7. Go to "OAuth2" → "URL Generator"
8. Select scopes: `bot`
9. Select permissions: `Send Messages`, `Read Messages/View Channels`, `Read Message History`
10. Copy the generated URL and open it to invite the bot to your server (or just use it for DMs)

### 5. Getting Your Discord User ID

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Developer Mode (toggle on)
2. Right-click your username anywhere in Discord
3. Click "Copy User ID"
4. Paste this ID into your `.env` file

### 6. Configure Craft API

You'll need:
- Your Craft API URL endpoint
- The endpoint should accept POST requests to `/daily-notes/today/blocks`
- Blocks should use the format: `{"type": "textBlock", "content": "..."}`

Update `CRAFT_API_URL` in your `.env` file with your Craft API base URL.

## Testing

### Test 1: Craft API Connection

Test that the bot can write to Craft:

```bash
python craft.py
```

This will attempt to write test blocks to today's daily note in Craft. Check your Craft app to verify they appear.

### Test 2: Discord Bot (Manual)

Run the bot locally:

```bash
python main.py
```

You should see:
```
Bot is ready! Logged in as YourBotName (ID: ...)
Scheduler started successfully
```

The bot is now running but won't respond to DMs unless it's expecting a check-in response.

### Test 3: Scheduler (Temporary Time)

To test the scheduler without waiting until 7:00 AM:

1. Edit `scheduler.py` temporarily
2. Change the cron triggers to a few minutes in the future:
   ```python
   # Example: if it's currently 2:35 PM, set to 2:37 PM
   scheduler.add_job(
       send_morning_checkin,
       trigger=CronTrigger(hour=14, minute=37, timezone=timezone),
       ...
   )
   ```
3. Run the bot: `python main.py`
4. Wait for the scheduled time
5. You should receive a DM from the bot
6. Reply to test the full flow
7. Check Craft to verify your response was added

**Remember to revert the schedule times before deploying!**

### Test 4: End-to-End Flow

1. Start the bot: `python main.py`
2. Manually trigger a check-in (use Test 3 method)
3. Receive the DM
4. Reply with your response
5. Verify:
   - Bot confirms: "Got it! Added to your Craft daily note ✅"
   - Your response appears in Craft's daily note
   - Bot logs show successful processing

## Deployment to Railway

### Prerequisites

- [Railway](https://railway.app/) account
- GitHub repository with your code

### Steps

1. **Push Code to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create Railway Project**

   - Go to [Railway](https://railway.app/)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect Python and the Procfile

3. **Set Environment Variables**

   In Railway project settings, add these variables:
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_USER_ID`
   - `CRAFT_API_URL`
   - `TIMEZONE`

4. **Deploy**

   Railway will automatically deploy. Monitor the logs to verify:
   - "Bot is ready! Logged in as..."
   - "Scheduler started successfully"

5. **Verify Deployment**

   - Check Railway logs for any errors
   - Wait for the next scheduled check-in time
   - Or temporarily modify schedule times to test sooner

## Timezone Configuration

The bot uses the `TIMEZONE` environment variable to schedule check-ins in your local time.

Common timezone values:
- `America/New_York` (Eastern)
- `America/Chicago` (Central)
- `America/Denver` (Mountain)
- `America/Los_Angeles` (Pacific)
- `Europe/London`
- `Asia/Tokyo`

See [pytz timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a full list.

## Project Structure

```
DiscordCoachBot/
├── main.py              # Discord bot core and message handling
├── scheduler.py         # APScheduler configuration and check-in jobs
├── craft.py            # Craft API client and formatting logic
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .env               # Your local environment variables (not in git)
├── .gitignore         # Git ignore rules
├── Procfile           # Railway deployment configuration
└── README.md          # This file
```

## How It Works

1. **Scheduler runs** at configured times (7:00 AM and 5:30 PM)
2. **Bot sends DM** asking about routine/exercise
3. **Conversation state** is set to wait for response
4. **User replies** via DM
5. **Bot receives message**, validates it's from the correct user
6. **Response is formatted** with headers and timestamps
7. **Craft API** receives the formatted block
8. **Bot confirms** to user that response was saved
9. **State is cleared** for the next check-in

## Troubleshooting

### Bot doesn't respond to DMs

- Make sure you're DMing from the correct Discord account (matching `DISCORD_USER_ID`)
- Check if conversation state is active (bot only responds during check-ins)
- Verify bot has DM permissions and you haven't blocked it

### Craft API errors

- Verify `CRAFT_API_URL` is correct
- Check Craft API is accessible (test with `python craft.py`)
- Review bot logs for specific error messages
- Ensure Craft API endpoint accepts the expected block format

### Scheduler not firing

- Verify `TIMEZONE` is set correctly
- Check Railway logs for scheduler initialization
- Ensure the bot process is running continuously
- Temporarily change times to verify scheduler is working

### Bot crashes or restarts

- Check Railway logs for error messages
- Verify all environment variables are set
- Ensure dependencies are installed correctly
- Check for network/API connectivity issues

## Future Enhancements

Potential features to add:
- Weekly finance reminder check-in
- Custom check-in messages
- Multiple users support
- Web dashboard for viewing responses
- Response analytics and streaks

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
