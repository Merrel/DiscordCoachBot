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
from scheduler import start_scheduler, get_next_checkin_time
from state import get_waiting_state, clear_waiting_state, set_waiting_for_checkin

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

        # Get message content
        content = message.content.strip()
        check_in_type = get_waiting_state()

        # Handle commands (start with /)
        if content.startswith('/'):
            await self.handle_command(message, content)
            return

        # If waiting for check-in response, process it
        if check_in_type is not None:
            await self.process_checkin_response(message, check_in_type)
            return

        # Handle casual messages when not in check-in mode
        await self.handle_casual_message(message, content)

    async def handle_command(self, message, content):
        """Handle slash commands."""
        command = content.lower().split()[0]

        if command == '/morning':
            # Trigger manual morning check-in
            set_waiting_for_checkin('morning')
            await message.channel.send(
                "Good morning! 🌅\n\n"
                "Did you complete your morning routine today?\n\n"
                "Please share how it went!"
            )
            logger.info("Manual morning check-in triggered")

        elif command == '/evening':
            # Trigger manual evening check-in
            set_waiting_for_checkin('evening')
            await message.channel.send(
                "Evening check-in! 💪\n\n"
                "Did you get your exercise in today?\n\n"
                "Let me know how it went!"
            )
            logger.info("Manual evening check-in triggered")

        elif command == '/status':
            # Show next scheduled check-in
            next_checkin = get_next_checkin_time()
            if next_checkin:
                await message.channel.send(
                    f"📅 **Status**\n\n"
                    f"Next scheduled check-in:\n"
                    f"{next_checkin}"
                )
            else:
                await message.channel.send(
                    "Scheduler is running. Check-ins at 7:00 AM and 5:30 PM MT."
                )

        elif command == '/help':
            # Show available commands
            await message.channel.send(
                "🤖 **Coach Bot - Available Commands**\n\n"
                "**Manual Check-ins:**\n"
                "`/morning` - Start morning routine check-in\n"
                "`/evening` - Start exercise check-in\n\n"
                "**Info:**\n"
                "`/status` - Show next scheduled check-in\n"
                "`/help` - Show this help message\n\n"
                "**Scheduled Check-ins:**\n"
                "• Morning: 7:00 AM MT\n"
                "• Evening: 5:30 PM MT\n\n"
                "Your responses are automatically saved to your Craft daily notes!"
            )

        else:
            await message.channel.send(
                f"Unknown command: {command}\n\n"
                f"Try `/help` to see available commands."
            )

    async def process_checkin_response(self, message, check_in_type):
        """Process a check-in response."""
        user_response = message.content
        logger.info(f"Received {check_in_type} check-in response from user")

        try:
            success = await write_to_daily_note(user_response, check_in_type)

            if success:
                clear_waiting_state()
                await message.channel.send(
                    "Got it! Added to your Craft daily note ✅"
                )
                logger.info(f"Successfully processed {check_in_type} check-in")
            else:
                await message.channel.send(
                    "Received your response, but there was an issue writing to Craft. "
                    "I'll log it for troubleshooting."
                )
                logger.error(f"Failed to write {check_in_type} check-in to Craft")
                clear_waiting_state()

        except Exception as e:
            logger.error(f"Error processing check-in response: {e}")
            await message.channel.send(
                "Sorry, I encountered an error processing your response. "
                "Please check the logs."
            )
            clear_waiting_state()

    async def handle_casual_message(self, message, content):
        """Handle casual messages outside of check-in mode."""
        content_lower = content.lower()

        # Greetings
        if content_lower in ['hi', 'hello', 'hey', 'yo', 'sup']:
            await message.channel.send(
                "Hey there! 👋\n\n"
                "I'm your daily check-in coach. I'll message you at:\n"
                "• 7:00 AM for your morning routine\n"
                "• 5:30 PM for your exercise\n\n"
                "Want to do a check-in now? Try `/morning` or `/evening`\n"
                "Need help? Send `/help`"
            )

        # Thanks
        elif any(word in content_lower for word in ['thanks', 'thank you', 'thx']):
            await message.channel.send(
                "You're welcome! Keep up the great work! 💪"
            )

        # Generic fallback
        else:
            await message.channel.send(
                "I'm here to help with your daily check-ins!\n\n"
                "Try:\n"
                "• `/morning` - Morning routine check-in\n"
                "• `/evening` - Exercise check-in\n"
                "• `/help` - See all commands\n\n"
                "Or just wait for my scheduled messages at 7 AM and 5:30 PM! ⏰"
            )


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
