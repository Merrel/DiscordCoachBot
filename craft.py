"""
Craft API client for writing check-in responses to daily notes.
"""

import os
import logging
from datetime import datetime
import httpx
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

CRAFT_API_URL = os.getenv('CRAFT_API_URL')


def format_check_in_content(content: str, check_in_type: str) -> str:
    """
    Format the check-in content with appropriate headers and structure.

    Args:
        content: The user's response text
        check_in_type: Either 'morning' or 'evening'

    Returns:
        Formatted markdown content
    """
    timestamp = datetime.now().strftime('%I:%M %p')

    if check_in_type == 'morning':
        # Parse for completion keywords
        completion_status = ""
        content_lower = content.lower()
        if 'yes' in content_lower and 'no' not in content_lower:
            completion_status = "Yes"
        elif 'partial' in content_lower:
            completion_status = "Partial"
        elif 'no' in content_lower:
            completion_status = "No"

        formatted = f"## Morning Check-in ({timestamp})\n"
        if completion_status:
            formatted += f"**Routine completion:** {completion_status}\n"
        formatted += f"{content}"

    elif check_in_type == 'evening':
        # Parse for workout keywords
        workout_status = ""
        content_lower = content.lower()
        if 'yes' in content_lower and 'no' not in content_lower:
            workout_status = "Yes"
        elif 'no' in content_lower:
            workout_status = "No"

        formatted = f"## Exercise Check-in ({timestamp})\n"
        if workout_status:
            formatted += f"**Workout:** {workout_status}\n"
        formatted += f"{content}"

    else:
        formatted = content

    return formatted


async def write_to_daily_note(content: str, check_in_type: str) -> bool:
    """
    Write check-in content to today's Craft daily note.

    Args:
        content: The user's response text
        check_in_type: Either 'morning' or 'evening'

    Returns:
        True if successful, False otherwise
    """
    if not CRAFT_API_URL:
        logger.error("CRAFT_API_URL not configured in environment variables")
        return False

    # Format the content
    formatted_content = format_check_in_content(content, check_in_type)

    # Prepare the API request using Craft's correct format
    request_data = {
        "blocks": [
            {
                "type": "text",
                "markdown": formatted_content
            }
        ],
        "position": {
            "position": "end",
            "date": "today"
        }
    }

    endpoint = f"{CRAFT_API_URL}/blocks"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                endpoint,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully wrote {check_in_type} check-in to Craft")
                return True
            else:
                logger.error(
                    f"Craft API error: {response.status_code} - {response.text}"
                )
                return False

    except httpx.TimeoutException:
        logger.error("Timeout while connecting to Craft API")
        return False
    except httpx.RequestError as e:
        logger.error(f"Request error while writing to Craft: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error writing to Craft: {e}")
        return False


# Test function
if __name__ == "__main__":
    import asyncio

    async def test_craft_api():
        """Test the Craft API connection with sample data."""
        print("Testing Craft API connection...")

        # Test morning check-in
        test_content_morning = "Yes, I completed my morning routine! Feeling energized."
        success = await write_to_daily_note(test_content_morning, "morning")
        print(f"Morning check-in test: {'SUCCESS' if success else 'FAILED'}")

        # Test evening check-in
        test_content_evening = "Yes, did a 30-minute run today."
        success = await write_to_daily_note(test_content_evening, "evening")
        print(f"Evening check-in test: {'SUCCESS' if success else 'FAILED'}")

    asyncio.run(test_craft_api())
