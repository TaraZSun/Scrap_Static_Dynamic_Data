from typing import Callable, Any, Optional, Awaitable
import asyncio
import requests
import logging
import sys
from functools import wraps


def retry_async(max_retries:int, delay_seconds:float):
    """
    Decorator to retry an acnync function on exception.
    """
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func) 
        async def wrapper(*args, **kwargs)->Optional[Any]:
            for attempt in range(max_retries+1):
                is_last_attempt = attempt == max_retries
                try:
                    logging.info(f"Attempt {attempt+1} of {max_retries+1}")
                    result = await func(*args, **kwargs)

                    if result is not None:
                        return result
                    
                    if not is_last_attempt:
                        logging.warning(f"Retrying after {delay_seconds} seconds...")
                        await asyncio.sleep(delay_seconds)
                        continue
                    logging.error("Max retries reached. The request failed with empty result. Stopping retries.")
                    sys.exit(1)

                except (Exception, requests.RequestException) as e:
                    logging.error(f"Error on attempt {attempt+1}: {e}")
                    if is_last_attempt:
                        logging.error("Max retries reached. The request failed with empty result. Stopping retries.")
                        sys.exit(1)

                    logging.info(f"Retrying after {delay_seconds} seconds...")
                    await asyncio.sleep(delay_seconds)
           
        return wrapper
    return decorator