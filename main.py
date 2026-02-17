"""
Discord Coach Bot - Main entry point
Sends scheduled check-ins and writes responses to Craft daily notes.
"""

import os
import logging
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
from craft import write_to_daily_note
from scheduler import start_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_USER_ID = os.getenv('DISCORD_USER_ID')

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
if not DISCORD_USER_ID:
    raise ValueError("DISCORD_USER_ID not found in environment variables")

# Convert user ID to integer
DISCORD_USER_ID = int(DISCORD_USER_ID)

# Conversation state tracking
conversation_state = {
    'waiting_for': None,  # 'morning', 'evening', or None
    'last_check_in_time': None
}


class CoachBot(discord.Client):
    """Discord bot client for coach check-ins."""

    def __init__(self):
        # Set up intents for DMs and message content
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.members = True

        super().__init__(intents=intents)
        self.scheduler = None

    async def on_ready(self):
        """Called when the bot is ready and connected."""
        logger.info(f'Bot is ready! Logged in as {self.user.name} (ID: {self.user.id})')

        # Start the scheduler
        self.scheduler = start_scheduler(self)
        logger.info('Scheduler started successfully')

    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # Only respond to DMs from the configured user
        if not isinstance(message.channel, discord.DMChannel):
            return

        if message.author.id != DISCORD_USER_ID:
            logger.warning(
                f"Received DM from unauthorized user: {message.author.id}"
            )
            return

        # Check if we're waiting for a response
        if conversation_state['waiting_for'] is None:
            # Not waiting for a check-in response
            logger.info(
                f"Received message while not waiting for check-in: {message.content[:50]}"
            )
            return

        # We have a check-in response
        check_in_type = conversation_state['waiting_for']
        user_response = message.content

        logger.info(f"Received {check_in_type} check-in response from user")

        # Write to Craft
        try:
            success = await write_to_daily_note(user_response, check_in_type)

            if success:
                # Clear conversation state
                conversation_state['waiting_for'] = None
                conversation_state['last_check_in_time'] = datetime.now()

                # Send confirmation
                await message.channel.send(
                    "Got it! Added to your Craft daily note ✅"
                )
                logger.info(f"Successfully processed {check_in_type} check-in")
            else:
                # Craft API failed
                await message.channel.send(
                    "Received your response, but there was an issue writing to Craft. "
                    "I'll log it for troubleshooting."
                )
                logger.error(f"Failed to write {check_in_type} check-in to Craft")

                # Still clear the state so we don't keep trying
                conversation_state['waiting_for'] = None

        except Exception as e:
            logger.error(f"Error processing check-in response: {e}")
            await message.channel.send(
                "Sorry, I encountered an error processing your response. "
                "Please check the logs."
            )
            # Clear state to prevent getting stuck
            conversation_state['waiting_for'] = None


def main():
    """Main entry point for the bot."""
    # Create and run the bot
    bot = CoachBot()

    try:
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise


if __name__ == "__main__":
    main()
