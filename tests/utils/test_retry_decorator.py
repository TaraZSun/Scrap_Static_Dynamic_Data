import pytest
import asyncio
from unittest import mock
from src.utils import decorators

def create_failing_async_function(fail_times, return_value="SUCCESS", fail_type=Exception):
    """
    Creates an async function that fails a specified number of times before returning a value.
    """
    attempt_count = [0]

    async def mock_func(*args, **kwargs):
        current_attempt = attempt_count[0]
        attempt_count[0] += 1

        if current_attempt < fail_times:
            if fail_type is Exception:
                raise ValueError(f"Simulated failure on attempt {current_attempt + 1}")
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
    decorator_func = decorators.retry_async(max_retries=max_retries, delay_seconds=0.1)(mock_target)
    mocker.patch("asyncio.sleep", new=mock.AsyncMock())  # Speed up sleep in tests
    result = await decorator_func(1, key="test")
    assert result == "SUCCESS"
    assert attempt_count[0] == fail_times
    assert asyncio.sleep.call_count == 1

@pytest.mark.asyncio
async def test_retry_on_none_return_success(mocker):
    """
    Test that the retry_async decorator retries the function on None return and eventually succeeds.
    """
    fail_times = 2
    max_retries = 3
    
    mock_target, attempt_count = create_failing_async_function(
        fail_times=fail_times-1, 
        fail_type=None)
    decorator_func = decorators.retry_async(max_retries=max_retries, delay_seconds=0.1)(mock_target)
    mocker.patch("asyncio.sleep", new=mock.AsyncMock())
    result = await decorator_func()
    assert result == "SUCCESS"
    assert attempt_count[0] == fail_times
    assert asyncio.sleep.call_count == 2

@pytest.mark.asyncio
async def test_retry_on_exception_max_retries_reached(mocker):
    """
    Test that the retry_async decorator stops retrying after max_retries is reached on exceptions.
    """
    max_retries = 2
    
    mock_target, _ = create_failing_async_function(
        fail_times=max_retries + 1, 
        fail_type=Exception)
    decorator_func = decorators.retry_async(max_retries=max_retries, delay_seconds=0.1)(mock_target)
    mocker.patch("asyncio.sleep", new=mock.AsyncMock())
    
    with pytest.raises(SystemExit) as excinfo:
        await decorator_func()
    assert excinfo.value.code==1
    assert asyncio.sleep.call_count == max_retries

@pytest.mark.asyncio
async def test_retry_on_none_return_max_retries_reached(mocker):
    """
    Test that the retry_async decorator stops retrying after max_retries is reached on None returns.
    """
    max_retries = 2
    
    mock_target, _ = create_failing_async_function(
        fail_times=max_retries + 1, 
        fail_type=None)
    decorator_func = decorators.retry_async(max_retries=max_retries, delay_seconds=0.1)(mock_target)
    mocker.patch("asyncio.sleep", new=mock.AsyncMock())
    
    with pytest.raises(SystemExit) as excinfo:
        await decorator_func()
    assert excinfo.value.code==1
    assert asyncio.sleep.call_count == max_retries


