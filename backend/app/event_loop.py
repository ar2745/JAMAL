import asyncio
import logging
import platform

logger = logging.getLogger(__name__)

def configure_event_loop():
    """
    Configure the event loop based on the operating system.
    On Windows, this sets up the ProactorEventLoop to handle async I/O properly.
    """
    if platform.system() == "Windows":
        try:
            # Set the event loop policy to WindowsProactorEventLoopPolicy
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            logger.info("Configured Windows ProactorEventLoop")
        except Exception as e:
            logger.error(f"Failed to configure Windows event loop: {e}")
            raise
    else:
        try:
            # For non-Windows systems, use the default event loop
            asyncio.get_event_loop()
            logger.info("Using default event loop")
        except Exception as e:
            logger.error(f"Failed to get default event loop: {e}")
            raise

def get_event_loop():
    """
    Get the configured event loop.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except Exception as e:
        logger.error(f"Failed to get event loop: {e}")
        raise 