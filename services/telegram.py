from aiogram import Bot
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def send_group_message(group_id: str, message_text: str, bot: Bot):
    """
    Sends a formatted message to the specified group chat.
    """
    if not group_id:
        logger.warning("WARNING: group_id is missing or invalid. Skipping Telegram send.")
        return

    try:
        await bot.send_message(
            chat_id=group_id,
            text=message_text,
            parse_mode='HTML'
        )
        logger.info("Successfully sent notification to group.")
    except Exception as e:
        # Common error: Token is wrong, or the bot was removed from the group
        logger.error(f"ERROR: sending message to Telegram group {group_id}: {e}")
