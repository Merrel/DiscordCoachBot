"""
Shared conversation state for the Discord Coach Bot.
This module ensures state is shared correctly between main.py and scheduler.py
"""

from datetime import datetime
from typing import Optional

# Shared conversation state
conversation_state = {
    'waiting_for': None,  # 'morning', 'evening', or None
    'last_check_in_time': None
}


def set_waiting_for_checkin(check_in_type: str):
    """Set the bot to wait for a specific check-in response."""
    conversation_state['waiting_for'] = check_in_type
    conversation_state['last_check_in_time'] = datetime.now()


def clear_waiting_state():
    """Clear the waiting state after processing a response."""
    conversation_state['waiting_for'] = None


def get_waiting_state() -> Optional[str]:
    """Get the current waiting state."""
    return conversation_state['waiting_for']
