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

def get_links(page_url):
    if page_url in page_cache:
        logs.append(f"Page found in cache: {page_url}")
        all_links = page_cache[page_url]
    else:
        logs.append(f"Fetching page: {page_url}")
        response = requests.get(page_url)
        logs.append(f"Finished fetching page: {page_url}")
        soup = BeautifulSoup(response.text, 'html.parser')
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

def find_path(start_page, finish_page):
    start_time = time.time()
    logs = []
    queue = Queue()
    discovered = {start_page: [start_page]}
    queue.put((start_page, [start_page], 0))

    while not queue.empty():
        vertex, path, depth = queue.get()
        if vertex == finish_page:
            elapsed_time = time.time() - start_time
            log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered), depth)
            return path, logs, elapsed_time, len(discovered)
        if depth > MAX_DEPTH:
            continue
        for next in set(get_links(vertex)) - set(discovered.keys()):
            discovered[next] = path + [next]
            queue.put((next, path + [next], depth + 1))
    elapsed_time = time.time() - start_time
    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(discovered))
        if not queue.empty():
            vertex, path, depth = queue.get()
        if vertex in other_discovered:
            return path + other_discovered[vertex][::-1]
        if depth > MAX_DEPTH:
            return None
        for next in set(get_links(vertex)) - set(discovered.keys()):
            discovered[next] = path + [next]
            queue.put((next, path + [next], depth + 1))
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
