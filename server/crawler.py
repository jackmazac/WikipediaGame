import asyncio
import aiohttp
import csv
import os
import re
import time
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin

TIMEOUT = 20  # Time limit in seconds for the search
MAX_DEPTH = 5  # Maximum depth for the search to prevent going too deep
page_cache = {}

wiki_link_pattern = re.compile(r'^https://en\.wikipedia\.org/wiki/[^:]*$')

from retrying import retry

def is_retryable_exception(exception):
    """Determine if the exception is due to a retryable error."""
    return isinstance(exception, (aiohttp.ClientError, asyncio.TimeoutError))

@retry(retry_on_exception=is_retryable_exception, stop_max_attempt_number=3, wait_fixed=2000)
async def get_links(session, page_url):
    global page_cache
    # Removed semaphore usage as it's not needed in distributed mode
    async with semaphore:
        cached_links = await page_cache.get(page_url)
        if cached_links:
            logs.append(f"Page found in cache: {page_url}")
            all_links = json.loads(cached_links)
        else:
            logs.append(f"Fetching page: {page_url}")
            try:
                response = await session.get(page_url)
                if response.status == 200:
                    response_text = await response.text()
                else:
                    logs.append(f"Error fetching page: {page_url}, status code: {response.status}")
                    return []
            except Exception as e:
                logs.append(f"Exception fetching page: {page_url}, error: {str(e)}")
                return []
            logs.append(f"Finished fetching page: {page_url}")
            soup = BeautifulSoup(response_text, 'html.parser')
            all_links = [urljoin(page_url, a['href']) for a in soup.find_all('a', href=True) if wiki_link_pattern.match(urljoin(page_url, a['href']))]
            await page_cache.setex(page_url, 3600, json.dumps(all_links))  # Cache with expiration
        logs.append(f"Found {len(all_links)} links on page: {page_url}")
        return all_links

def log_performance_metrics(start_page, finish_page, elapsed_time, discovered_pages_count, depth_reached):
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
from queue import Queue
from urllib.parse import urljoin

async def find_path(start_page, finish_page, timeout=TIMEOUT):
    start_time = time.time()
    logs = []
    queue = deque()
    discovered = {start_page: [start_page]}
    queue.append((start_page, [start_page], 0))
    async with aiohttp.ClientSession() as session:
        while queue:
            vertex, path, depth = queue.popleft()
            if vertex == finish_page:
                elapsed_time = time.time() - start_time
                log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered), depth)
                return path, logs, elapsed_time, len(discovered)
            if depth > MAX_DEPTH:
                continue
            links = await get_links(session, vertex)
            for next in set(links) - set(discovered.keys()):
                discovered[next] = path + [next]
                queue.append((next, path + [next], depth + 1))
    elapsed_time = time.time() - start_time
    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(discovered))



async def search_step(session, queue, discovered, other_discovered, reverse=False):
    if queue:
        vertex, path, depth = queue.popleft()
        if vertex in other_discovered:
            return path + other_discovered[vertex][::-1][1:]
        if depth > MAX_DEPTH:
            return None
        links = await get_links(session, vertex)
        for next in set(links) - set(discovered.keys()):
            discovered[next] = path + [next]
            queue.append((next, path + [next], depth + 1))
    return None

class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered
import asyncio
import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            while queue:
                vertex, path, depth = queue.popleft()
                if vertex == finish_page:
                    elapsed_time = time.time() - start_time
                    log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered), depth)
                    return path, logs, elapsed_time, len(discovered)
                if depth > MAX_DEPTH:
                    continue
                links = await get_links(session, vertex)
                for next in set(links) - set(discovered.keys()):
                    discovered[next] = path + [next]
                    queue.append((next, path + [next], depth + 1))
        elapsed_time = time.time() - start_time
        raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(discovered))
    except Exception as e:
        logs.append(f"Unexpected error: {str(e)}")
        raise TimeoutErrorWithLogs("An unexpected error occurred.", logs, time.time() - start_time, len(discovered))
CONCURRENT_REQUESTS_LIMIT = 10  # Limit for concurrent requests

import redis
from rq import Queue

redis_conn = redis.Redis()
distributed_queue = Queue(connection=redis_conn)
page_cache = redis_conn

CONCURRENT_REQUESTS_LIMIT = 20  # Adjusted limit for concurrent requests based on server's capacity
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)  # Reintroduced semaphore for concurrency control

def enqueue_link_fetching(session, page_url):
    job = distributed_queue.enqueue(get_links, session, page_url)
    return job.result


CONCURRENT_REQUESTS_LIMIT = 10  # Limit for concurrent requests
import redis
from rq import Queue

redis_conn = redis.Redis()
distributed_queue = Queue(connection=redis_conn)
page_cache = redis_conn

CONCURRENT_REQUESTS_LIMIT = 20  # Adjusted limit for concurrent requests based on server's capacity
semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)  # Reintroduced semaphore for concurrency control

def enqueue_link_fetching(session, page_url):
    job = distributed_queue.enqueue(get_links, session, page_url)
    return job.result

