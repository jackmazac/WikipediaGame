import time
from collections import deque
import requests
from bs4 import BeautifulSoup
import re
import csv
import os

TIMEOUT = 20  # time limit in seconds for the search
page_cache = {}
import re

wiki_link_pattern = re.compile(r'^https://en\.wikipedia\.org/wiki/[^:]*$')

def get_links(page_url, verbose=True):
    if page_url in page_cache:
        print(f"Page found in cache: {page_url}")
        all_links = page_cache[page_url]
    else:
        print(f"Fetching page: {page_url}")
        response = requests.get(page_url)
        print(f"Finished fetching page: {page_url}")
        soup = BeautifulSoup(response.text, 'html.parser')
        from urllib.parse import urljoin
        all_links = [urljoin(page_url, a['href']) for a in soup.find_all('a', href=True) if '#' not in a['href']]
        page_cache[page_url] = all_links
    if verbose:
        print(f"All links found: {all_links}")
    # print(f"All links found: {all_links}")
    links = [link for link in all_links if wiki_link_pattern.match(link)]
    print(f"Found {len(links)} links on page: {page_url}")
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
from queue import PriorityQueue
import difflib

def url_similarity(url1, url2):
    return difflib.SequenceMatcher(None, url1, url2).ratio()

def find_path(start_page, finish_page):
    queue = deque([(start_page, [start_page], 0)])
    queue = PriorityQueue()
    discovered = set()
    logs = []

    # breadth first search
    start_time = time.time()
    elapsed_time = time.time() - start_time
    queue.put((0, start_page, [start_page], 0))  # Priority, vertex, path, depth
    while not queue.empty() and elapsed_time < TIMEOUT:
        _, vertex, path, depth = queue.get()
        for next in set(get_links(vertex)) - discovered:
            if next == finish_page:
                log = f"Found finish page: {next}"
                print(log)
                logs.append(log)
                logs.append(f"Search took {elapsed_time} seconds.")
                print(f"Search took {elapsed_time} seconds.")  # Add a print statement to log the elapsed time
                logs.append(f"Discovered pages: {len(discovered)}")
                return path + [next], logs, elapsed_time, len(discovered) # return with success
            else:
                log = f"Adding link to queue: {next} (depth {depth})"
                print(log)
                logs.append(log)
                discovered.add(next)
                similarity = url_similarity(next, finish_page)
                priority = -similarity  # Negative because PriorityQueue returns lowest first
                queue.put((priority, next, path + [next], depth + 1))
        elapsed_time = time.time() - start_time
        depth_reached = depth
    logs.append(f"Search took {elapsed_time} seconds.")
    print(f"Search took {elapsed_time} seconds.")  # Add a print statement to log the elapsed time
    logs.append(f"Discovered pages: {len(discovered)}")
    log_performance_metrics(start_page, finish_page, elapsed_time, len(discovered), depth_reached)
    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(discovered))
class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered
