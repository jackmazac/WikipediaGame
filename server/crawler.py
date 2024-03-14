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

# Constants for configuring the behavior of the crawler
TIMEOUT = 60  # Time limit in seconds for the search
MAX_DEPTH = 10  # Maximum depth for the search to prevent going too deep
CONCURRENT_REQUESTS_LIMIT = 10  # Limit for concurrent requests

# Compile a pattern to match valid Wikipedia article links
wiki_link_pattern = re.compile(r'^https://en\.wikipedia\.org/wiki/[^:]*$')

# Initialize a connection to Redis for caching
import redis
from rq import Queue as RQQueue

redis_conn = redis.Redis()
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
            return json.loads(cached_links)

        async with session.get(page_url) as response:
            if response.status == 200:
                response_text = await response.text()
                soup = BeautifulSoup(response_text, 'html.parser')
                all_links = [urljoin(page_url, a['href']) for a in soup.find_all('a', href=True) if wiki_link_pattern.match(urljoin(page_url, a['href']))]
                redis_conn.setex(page_url, 3600, json.dumps(all_links))  # Cache with expiration
                return all_links
            else:
                return []
    except Exception as e:
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

async def bidirectional_search(start_page, finish_page):
    """Perform a bidirectional search between the start_page and finish_page."""
    start_time = time.time()
    start_queue = deque([(start_page, [start_page])])
    finish_queue = deque([(finish_page, [finish_page])])
    discovered_from_start = {start_page: [start_page]}
    discovered_from_finish = {finish_page: [finish_page]}
    
    async with aiohttp.ClientSession() as session:
        while start_queue and finish_queue:
            # Expand from the start side
            if start_queue:
                await search_step(session, start_queue, discovered_from_start, discovered_from_finish)
            # Expand from the finish side
            if finish_queue:
                await search_step(session, finish_queue, discovered_from_finish, discovered_from_start)
                
            # Check for intersection
            intersect_node = set(discovered_from_start.keys()).intersection(set(discovered_from_finish.keys()))
            if intersect_node:
                # Path found
                intersect_node = intersect_node.pop()
                path_from_start = discovered_from_start[intersect_node]
                path_from_finish = discovered_from_finish[intersect_node][::-1]
                total_path = path_from_start + path_from_finish[1:]  # remove duplicate intersect node
                elapsed_time = time.time() - start_time
                log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered_from_start) + len(discovered_from_finish), max(len(path_from_start), len(path_from_finish)))
                return total_path

    elapsed_time = time.time() - start_time
    log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered_from_start) + len(discovered_from_finish), MAX_DEPTH + 1)
    return None  # Path not found within depth limit

async def search_step(session, queue, discovered, other_discovered):
    """A step in the bidirectional search, expanding the frontier from one side."""
    if queue:
        vertex, path = queue.popleft()
        if vertex in other_discovered:
            return path + other_discovered[vertex][::-1][1:]
        
        links = await get_links(session, vertex)
        for next_page in set(links) - set(discovered.keys()):
            discovered[next_page] = path + [next_page]
            queue.append((next_page, path + [next_page]))

# Define a new exception class for scenarios where no path is found within the depth limit
class PathNotFoundError(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered

# To start the bidirectional search:
# asyncio.run(bidirectional_search('https://en.wikipedia.org/wiki/Start_Page', 'https://en.wikipedia.org/wiki/End_Page'))import json

class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered

async def find_path(start_page, finish_page):
    try:
        path = await bidirectional_search(start_page, finish_page)
        if path is None:
            raise PathNotFoundError("Path not found within depth limit", [], TIMEOUT, 0)
        # Assuming logs, time, and discovered are calculated within bidirectional_search or elsewhere
        logs = ["Log entries here"]  # Placeholder for actual log entries
        time = 10  # Placeholder for actual time taken
        discovered = 100  # Placeholder for actual pages discovered
        return path, logs, time, discovered
    except asyncio.TimeoutError:
        raise PathNotFoundError("Path not found within depth limit", [], TIMEOUT, 0)
    except Exception as e:
        raise TimeoutErrorWithLogs(str(e), [], 0, 0)
