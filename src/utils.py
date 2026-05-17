# utils.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional
from tqdm import tqdm
import os
import logging

logger = logging.getLogger(__name__)


def multi_thread(
    items: List[Any],
    func: Callable,
    max_workers: Optional[int] = (os.cpu_count() or 1) * 5,
) -> List[Any]:
    """
    Executes a function concurrently for each item in the list.

    Args:
        items (List[Any]):
            List of inputs.

        func (Callable):
            Function to execute for each item.
            Example:
                def process(item):
                    return item * 2

        max_workers (Optional[int]):
            Number of threads to use.
            Default: Python decides automatically.

    Returns:
        List[Any]:
            Results in the same order as input items.
    """

    results = [None] * len(items)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(func, item): index
            for index, item in enumerate(items)
        }

        for future in tqdm(as_completed(future_to_index), total=len(items), desc="Processing items"):
            index = future_to_index[future]

            try:
                results[index] = future.result()
            except Exception as e:
                results[index] = e

    return results