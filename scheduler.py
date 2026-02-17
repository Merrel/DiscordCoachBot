"""
Scheduler for sending daily check-in messages.
"""

import os
import logging
from datetime import datetime
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv
from state import set_waiting_for_checkin

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate environment variables
discord_user_id_str = os.getenv('DISCORD_USER_ID')
if not discord_user_id_str:
    raise ValueError(
        "DISCORD_USER_ID environment variable is not set. "
        "Please set it in your .env file or Railway environment variables."
    )

try:
    DISCORD_USER_ID = int(discord_user_id_str)
except ValueError:
    raise ValueError(
        f"DISCORD_USER_ID must be a valid integer, got: {discord_user_id_str}"
    )

TIMEZONE = os.getenv('TIMEZONE', 'America/Denver')


async def send_morning_checkin(bot_client: discord.Client):
    """
    Send the morning check-in message at 7:00 AM.

    Args:
        bot_client: The Discord bot client instance
    """
    try:
        # Get the user
        user = await bot_client.fetch_user(DISCORD_USER_ID)
        if not user:
            logger.error(f"Could not find user with ID: {DISCORD_USER_ID}")
            return

        # Send DM
        message = (
            "Good morning! 🌅\n\n"
            "Did you complete your morning routine today?\n\n"
            "Please share how it went!"
        )

        await user.send(message)

        # Set conversation state
        set_waiting_for_checkin('morning')

        logger.info("Morning check-in sent successfully")

    except discord.Forbidden:
        logger.error(
            f"Cannot send DM to user {DISCORD_USER_ID}. "
            "User may have DMs disabled or bot is blocked."
        )
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending morning check-in: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending morning check-in: {e}")


async def send_evening_checkin(bot_client: discord.Client):
    """
    Send the evening check-in message at 5:30 PM.

    Args:
        bot_client: The Discord bot client instance
    """
    try:
        # Get the user
        user = await bot_client.fetch_user(DISCORD_USER_ID)
        if not user:
            logger.error(f"Could not find user with ID: {DISCORD_USER_ID}")
            return

        # Send DM
        message = (
            "Evening check-in! 💪\n\n"
            "Did you get your exercise in today?\n\n"
            "Let me know how it went!"
        )

        await user.send(message)

        # Set conversation state
        set_waiting_for_checkin('evening')

        logger.info("Evening check-in sent successfully")

    except discord.Forbidden:
        logger.error(
            f"Cannot send DM to user {DISCORD_USER_ID}. "
            "User may have DMs disabled or bot is blocked."
        )
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending evening check-in: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending evening check-in: {e}")


def start_scheduler(bot_client: discord.Client) -> AsyncIOScheduler:
    """
    Initialize and start the APScheduler for daily check-ins.

    Args:
        bot_client: The Discord bot client instance

    Returns:
        The started scheduler instance
    """
    # Create scheduler with configured timezone
    timezone = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=timezone)

    # Schedule morning check-in at 7:00 AM
    scheduler.add_job(
        send_morning_checkin,
        trigger=CronTrigger(hour=7, minute=0, timezone=timezone),
        args=[bot_client],
        id='morning_checkin',
        name='Morning Check-in (7:00 AM)',
        replace_existing=True
    )

    # Schedule evening check-in at 5:30 PM
    scheduler.add_job(
        send_evening_checkin,
        trigger=CronTrigger(hour=17, minute=30, timezone=timezone),
        args=[bot_client],
        id='evening_checkin',
        name='Evening Check-in (5:30 PM)',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()

    logger.info(
        f"Scheduler started with timezone: {TIMEZONE}\n"
        f"  - Morning check-in: 7:00 AM\n"
        f"  - Evening check-in: 5:30 PM"
    )

    return scheduler


def get_next_checkin_time() -> str:
    """
    Get a formatted string of the next scheduled check-in time.

    Returns:
        Formatted string with next check-in info
    """
    from datetime import datetime, timedelta

    timezone = pytz.timezone(TIMEZONE)
    now = datetime.now(timezone)

    # Morning check-in at 7:00 AM
    morning = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now > morning:
        # If past morning time, check tomorrow
        morning = morning + timedelta(days=1)

    # Evening check-in at 5:30 PM
    evening = now.replace(hour=17, minute=30, second=0, microsecond=0)
    if now > evening:
        # If past evening time, check tomorrow
        evening = evening + timedelta(days=1)

    # Find which is next
    if morning < evening:
        next_time = morning
        check_type = "Morning routine"
    else:
        next_time = evening
        check_type = "Exercise"

    # Format the time
    time_str = next_time.strftime("%A, %B %d at %I:%M %p %Z")

    return f"**{check_type}** check-in\n{time_str}"
