import pytest
import asyncio
from unittest import mock
from scrape_data.utils import decorators

def create_failing_async_function(fail_times, return_value="SUCCESS", fail_type=Exception):
    """
    Creates an async function that fails a specified number of times before returning a value.
    """
    attempt_count = [0]

    async def mock_func(*args, **kwargs):
        current_attempt = attempt_count[0]
        attempt_count[0] += 1

        if current_attempt < fail_times:
            if issubclass(fail_type, Exception):
                raise fail_type(f"Simulated failure on attempt {current_attempt + 1}")
            elif fail_type is None:
                return None
        return return_value
    return mock_func, attempt_count

@pytest.mark.asyncio
async def test_retry_async_success_after_failures(mocker):
    """
    Test that the retry_async decorator retries the function on failure and eventually succeeds.
    """
    fail_times = 2
    max_retries = 3
    
    mock_target, attempt_count = create_failing_async_function(
        fail_times=fail_times-1, 
        fail_type=Exception)
    decorator_func = decorators.retry_async(max_retries=max_retries, base_delay=0.01)(mock_target)
    mocker.patch("asyncio.sleep", new=mock.AsyncMock())  # Speed up sleep in tests
    result = await decorator_func(1, key="test")
    assert result == "SUCCESS"
    assert attempt_count[0] == fail_times
    assert asyncio.sleep.call_count == 1

@pytest.mark.asyncio
async def test_retry_on_none_return_success(mocker):
    fail_times = 2  
    max_retries = 3

    mock_target, attempt_count = create_failing_async_function(
        fail_times=fail_times - 1,  # fail once
        fail_type=None              # means "return None"
    )

    decorated = decorators.retry_async(
        max_retries=max_retries,
        base_delay=0.01,
        retry_on_none=True  
    )(mock_target)

    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    result = await decorated()

    assert result == "SUCCESS"
    assert attempt_count[0] == fail_times    # 2 total calls
    assert asyncio.sleep.call_count == 1   


@pytest.mark.asyncio
async def test_retry_on_exception_max_retries_reached(mocker):
    """
    Test that retry_async stops retrying after max_retries
    and raises the last exception.
    """
    max_retries = 2

    mock_target, _ = create_failing_async_function(
        fail_times=max_retries + 1,   # always fails
        fail_type=ValueError          # pick a concrete exception
    )
    decorated = decorators.retry_async(
        max_retries=max_retries,
        base_delay=0.01
    )(mock_target)

    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    # Expect the original exception, not SystemExit
    with pytest.raises(ValueError, match="Simulated failure"):
        await decorated()

    # sleep called once per retry
    assert asyncio.sleep.call_count == max_retries


@pytest.mark.asyncio
async def test_retry_on_none_return_max_retries_reached(mocker):
    """
    Test that the retry_async decorator stops retrying after max_retries is reached
    on None returns, and gives up returning None.
    """
    max_retries = 2

    # Function always returns None
    async def always_none():
        return None

    decorated = decorators.retry_async(
        max_retries=max_retries,
        base_delay=0.01
    )(always_none)

    mocker.patch("asyncio.sleep", new=mocker.AsyncMock())

    result = await decorated()

    # After retries, should just return None (not raise SystemExit)
    assert result is None
    assert asyncio.sleep.call_count == max_retries



