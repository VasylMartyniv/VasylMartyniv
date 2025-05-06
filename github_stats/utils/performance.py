import time
from typing import Any, Callable, Tuple, TypeVar, Optional, Union

T = TypeVar('T')


def measure_performance(
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
) -> Tuple[T, float]:
    """
    Measure execution time of a function.

    Args:
        func: Function to measure
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Tuple of (function result, execution time in seconds)
    """
    start = time.perf_counter()
    result = func(*args, **kwargs)
    execution_time = time.perf_counter() - start
    return result, execution_time


def format_execution_time(
        query_type: str,
        execution_time: float,
        result: Optional[Any] = None,
        whitespace: int = 0
) -> Union[Any, str]:
    """
    Format and print execution time.

    Args:
        query_type: Name of the operation being timed
        execution_time: Execution time in seconds
        result: Optional result to format and return
        whitespace: Whitespace padding for result formatting

    Returns:
        Formatted result if whitespace specified, otherwise raw result
    """
    print('{:<23}'.format(f'   {query_type}:'), end='')

    if execution_time > 1:
        print('{:>12}'.format(f'{execution_time:.4f} s'))
    else:
        print('{:>12}'.format(f'{execution_time * 1000:.4f} ms'))

    if whitespace:
        return f"{'{:,}'.format(result): <{whitespace}}"
    return result