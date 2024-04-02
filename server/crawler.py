import asyncio
import aiohttp
import csv
import os
import re
import time
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin
from retrying import retry
import logging
import json
import redis
from rq import Queue as RQQueue
from heapq import heappush, heappop

# Configure logging
logging.basicConfig(filename='crawler.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for configuring the behavior of the crawler
TIMEOUT = 60  # Time limit in seconds for the search
MAX_DEPTH = 10  # Maximum depth for the search to prevent going too deep
CONCURRENT_REQUESTS_LIMIT = 10  # Limit for concurrent requests

# Compile a pattern to match valid Wikipedia article links
wiki_link_pattern = re.compile(r'^/wiki/[^:]+$')

# Initialize a connection to Redis for caching
redis_conn = redis.Redis(host='localhost', port=6379)
distributed_queue = RQQueue(connection=redis_conn)
page_cache = redis_conn

def is_retryable_exception(exception):
    """Determine if the exception is due to a retryable error."""
    return isinstance(exception, (aiohttp.ClientError, asyncio.TimeoutError))

@retry(retry_on_exception=is_retryable_exception, stop_max_attempt_number=3, wait_fixed=2000)
async def get_links(session, page_url):
    """Fetch links from a given page_url, cache them, and return only valid Wikipedia article links."""
    try:
        cached_links = redis_conn.get(page_url)
        if cached_links:
            logging.debug(f"Using cached links for {page_url}")
            return json.loads(cached_links)

        async with session.get(page_url) as response:
            if response.status == 200:
                response_text = await response.text()
                soup = BeautifulSoup(response_text, 'html.parser')
                all_links = [urljoin('https://en.wikipedia.org', a['href']) for a in soup.find_all('a', href=True) if wiki_link_pattern.match(a['href'])]
                redis_conn.setex(page_url, 3600, json.dumps(all_links))  # Cache with expiration
                return all_links
            else:
                logging.warning(f"Failed to fetch links from {page_url}. Status code: {response.status}")
                return []
    except Exception as e:
        logging.error(f"Error fetching links from {page_url}: {str(e)}")
        return []

def log_performance_metrics(start_page, finish_page, elapsed_time, discovered_pages_count, depth_reached):
    """Log performance metrics of the search operation to a CSV file."""
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    log_file_path = os.path.join(logs_dir, 'performance_logs.csv')
    file_exists = os.path.isfile(log_file_path)
    with open(log_file_path, 'a', newline='') as csvfile:
        fieldnames = ['start_page', 'finish_page', 'elapsed_time', 'discovered_pages_count', 'depth_reached']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'start_page': start_page,
            'finish_page': finish_page,
            'elapsed_time': elapsed_time,
            'discovered_pages_count': discovered_pages_count,
            'depth_reached': depth_reached
        })

def get_page_priority(page, finish_page):
    """Calculate the priority of a page based on its similarity to the finish page."""
    page_title = page.split('/')[-1].replace('_', ' ')
    finish_title = finish_page.split('/')[-1].replace('_', ' ')
    common_words = set(page_title.split()).intersection(finish_title.split())
    priority = -len(common_words)  # Negative priority for closer similarity
    return priority

async def bidirectional_search(start_page, finish_page):
    """Perform a bidirectional search between the start_page and finish_page."""
    start_time = time.time()
    start_queue = [(0, start_page, [start_page], 0)]
    finish_queue = [(0, finish_page, [finish_page], 0)]
    discovered_from_start = {start_page: [start_page]}
    discovered_from_finish = {finish_page: [finish_page]}
    visited_from_start = set()
    visited_from_finish = set()
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)

    async with aiohttp.ClientSession() as session:
        while start_queue and finish_queue:
            # Check for timeout
            if time.time() - start_time > TIMEOUT:
                raise asyncio.TimeoutError("Search timed out")

            # Expand from the start side
            if start_queue:
                result = await search_step(session, start_queue, discovered_from_start, discovered_from_finish, visited_from_start, semaphore, finish_page)
                if result is not None:
                    return result

            # Expand from the finish side
            if finish_queue:
                result = await search_step(session, finish_queue, discovered_from_finish, discovered_from_start, visited_from_finish, semaphore, start_page)
                if result is not None:
                    return result

    elapsed_time = time.time() - start_time
    log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered_from_start) + len(discovered_from_finish), MAX_DEPTH + 1)
    return None  # Path not found within depth limit

async def search_step(session, queue, discovered, other_discovered, visited, semaphore, target_page):
    """A step in the bidirectional search, expanding the frontier from one side."""
    if queue:
        _, vertex, path, depth = heappop(queue)
        if depth > MAX_DEPTH:
            return None

        if vertex in visited:
            return None

        visited.add(vertex)

        if vertex in other_discovered:
            other_path = other_discovered[vertex]
            return path + other_path[::-1][1:]

        async with semaphore:
            links = await get_links(session, vertex)

        for next_page in set(links) - set(discovered.keys()):
            priority = get_page_priority(next_page, target_page)
            discovered[next_page] = path + [next_page]
            heappush(queue, (priority, next_page, path + [next_page], depth + 1))

    return None

class PathNotFoundError(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered

class PathFindingErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered

async def find_path_async(start_page, finish_page):
    """Asynchronous wrapper for find_path function."""
    start_time = time.time()
    try:
        path = await bidirectional_search(start_page, finish_page)
        if path is None:
            raise PathNotFoundError("Path not found within depth limit", [], TIMEOUT, 0)
        logs = ["Log entries here"]  # Placeholder for actual log entries
        time_taken = time.time() - start_time
        discovered_from_start = {}  # Initialize discovered_from_start
        discovered_from_finish = {}  # Initialize discovered_from_finish
        discovered = len(discovered_from_start) + len(discovered_from_finish)
        return path, logs, time_taken, discovered
    except asyncio.TimeoutError:
        raise PathNotFoundError("Path not found within time limit", [], TIMEOUT, 0)
    except Exception as e:
        raise PathFindingErrorWithLogs(str(e), [], 0, 0)

async def main(start_page, finish_page):
    try:
        path, logs, time_taken, discovered = await find_path_async(start_page, finish_page)
        logging.info(f"Path found: {path}")
        logging.info(f"Time taken: {time_taken} seconds")
        logging.info(f"Pages discovered: {discovered}")
    except PathNotFoundError as e:
        logging.error(f"Path not found: {str(e)}")
    except PathFindingErrorWithLogs as e:
        logging.error(f"Error occurred during path finding: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    start_page = 'https://en.wikipedia.org/wiki/Start_Page'
    finish_page = 'https://en.wikipedia.org/wiki/End_Page'
    asyncio.run(main(start_page, finish_page))