import time
from collections import deque
import requests
from bs4 import BeautifulSoup
import re
import csv
import os

TIMEOUT = 20  # Time limit in seconds for the search
MAX_DEPTH = 5  # Maximum depth for the search to prevent going too deep
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
from urllib.parse import urlparse

def url_similarity(url1, url2):
    # Extract paths from URLs and compare them
    path1 = urlparse(url1).path
    path2 = urlparse(url2).path
    # Use a simple heuristic based on the overlap of path segments
    segments1 = set(path1.split('/'))
    segments2 = set(path2.split('/'))
    common_segments = segments1.intersection(segments2)
    # Calculate similarity as the ratio of common segments to total unique segments
    total_segments = segments1.union(segments2)
    if not total_segments:
        return 0
    similarity = len(common_segments) / len(total_segments)
    return similarity

def find_path(start_page, finish_page):
    queue = PriorityQueue()
    discovered = set()
    logs = []

    # breadth first search
    start_time = time.time()
    elapsed_time = time.time() - start_time
    queue.put((0, start_page, [start_page], 0))  # Priority, vertex, path, depth. Initialize with start_page
    while not queue.empty() and elapsed_time < TIMEOUT:
        _, vertex, path, depth = queue.get()
        if depth > MAX_DEPTH:
            continue  # Skip adding new links if maximum depth is exceeded
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
                # Adjust priority calculation to better reflect path similarity
                # Higher similarity gives a lower (more negative) priority
                priority = -1 * similarity * 100  # Scale to make differences more pronounced
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
