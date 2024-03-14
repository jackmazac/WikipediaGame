import time, re
from collections import deque
import requests
from bs4 import BeautifulSoup
import csv
import os

TIMEOUT = 20  # Time limit in seconds for the search
MAX_DEPTH = 5  # Maximum depth for the search to prevent going too deep
page_cache = {}

wiki_link_pattern = re.compile(r'^https://en\.wikipedia\.org/wiki/[^:]*$')

async def get_links(session, page_url):
    if page_url in page_cache:
        logs.append(f"Page found in cache: {page_url}")
        all_links = page_cache[page_url]
    else:
        logs.append(f"Fetching page: {page_url}")
        async with session.get(page_url) as response:
            response_text = await response.text()
        logs.append(f"Finished fetching page: {page_url}")
        soup = BeautifulSoup(response_text, 'html.parser')
        all_links = [urljoin(page_url, a['href']) for a in soup.find_all('a', href=True) if '#' not in a['href']]
        page_cache[page_url] = all_links
    links = [link for link in all_links if wiki_link_pattern.match(link)]
    logs.append(f"Found {len(links)} links on page: {page_url}")
    return links

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

async def find_path(start_page, finish_page):
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


async def bidirectional_search(start_page, finish_page):
    start_time = time.time()
    start_queue = deque()
    finish_queue = deque()
    start_discovered = {start_page: [start_page]}
    finish_discovered = {finish_page: [finish_page]}
    start_queue.append((start_page, [start_page], 0))
    finish_queue.append((finish_page, [finish_page], 0))
    async with aiohttp.ClientSession() as session:
        while start_queue and finish_queue:
            start_path = await search_step(session, start_queue, start_discovered, finish_discovered)
            if start_path:
                elapsed_time = time.time() - start_time
                log_performance_metrics(start_page, finish_page, elapsed_time, len(start_discovered) + len(finish_discovered), len(start_path) - 1)
                return start_path, logs, elapsed_time, len(start_discovered) + len(finish_discovered)
            finish_path = await search_step(session, finish_queue, finish_discovered, start_discovered, reverse=True)
            if finish_path:
                elapsed_time = time.time() - start_time
                log_performance_metrics(start_page, finish_page, elapsed_time, len(start_discovered) + len(finish_discovered), len(finish_path) - 1)
                return finish_path[::-1], logs, elapsed_time, len(start_discovered) + len(finish_discovered)
    elapsed_time = time.time() - start_time
    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(start_discovered) + len(finish_discovered))

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

    start_queue = Queue()
    start_discovered = {start_page: [start_page]}
    start_queue.put((start_page, [start_page], 0))

    while not start_queue.empty():
        path = bidirectional_search(start_queue, start_discovered, True)
        if path:
            return path, logs, elapsed_time, len(start_discovered) + len(finish_discovered)

    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(start_discovered) + len(finish_discovered))
class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered
import asyncio
import aiohttp

