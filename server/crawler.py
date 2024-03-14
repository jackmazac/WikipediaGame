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
from urllib.parse import parse_qs
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def url_similarity(url1, url2):
    def extract_title_from_url(url):
        path = urlparse(url).path
        title = path.split('/')[-1]  # Get the last segment of the path as title
        title = title.replace('_', ' ')  # Replace underscores with spaces
        return title

    def semantic_similarity(text1, text2):
        words1 = word_tokenize(text1.lower())
        words2 = word_tokenize(text2.lower())
        words1 = [word for word in words1 if word not in stop_words]
        words2 = [word for word in words2 if word not in stop_words]
        common_words = set(words1).intersection(set(words2))
        total_words = set(words1).union(set(words2))
        if not total_words:
            return 0
        return len(common_words) / len(total_words)

    title1 = extract_title_from_url(url1)
    title2 = extract_title_from_url(url2)
    semantic_score = semantic_similarity(title1, title2)
    path_score = semantic_similarity(urlparse(url1).path, urlparse(url2).path)
    query_score = semantic_similarity(str(parse_qs(urlparse(url1).query)), str(parse_qs(urlparse(url2).query)))
    # Weighted average of scores: Titles are more important than paths, and paths more than queries
    similarity = (0.6 * semantic_score) + (0.3 * path_score) + (0.1 * query_score)
    return similarity

def find_path(start_page, finish_page, max_queue_size=100):
    def bidirectional_search(queue, discovered, other_discovered, is_forward):
        if queue.empty():
            return None
        _, similarity_score, vertex, path, depth = queue.get()
        if vertex in other_discovered:
            return path + other_discovered[vertex][::-1] if is_forward else other_discovered[vertex] + path[::-1]
        if depth > MAX_DEPTH:
            return None
        for next in set(get_links(vertex)) - set(discovered.keys()):
            discovered[next] = path + [next]
            similarity = url_similarity(next, finish_page if is_forward else start_page)
            new_similarity_score = similarity_score + similarity
            new_priority = -1 * new_similarity_score
            queue.put((new_priority, new_similarity_score, next, path + [next], depth + 1))
        return None

    start_queue = PriorityQueue()
    finish_queue = PriorityQueue()
    start_discovered = {start_page: [start_page]}
    finish_discovered = {finish_page: [finish_page]}
    start_queue.put((0, 0, start_page, [start_page], 0))
    finish_queue.put((0, 0, finish_page, [finish_page], 0))

    while not start_queue.empty() or not finish_queue.empty():
        path = bidirectional_search(start_queue, start_discovered, finish_discovered, True)
        if path:
            return path, logs, elapsed_time, len(start_discovered) + len(finish_discovered)
        path = bidirectional_search(finish_queue, finish_discovered, start_discovered, False)
        if path:
            return path, logs, elapsed_time, len(start_discovered) + len(finish_discovered)

    raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, elapsed_time, len(start_discovered) + len(finish_discovered))
    queue = PriorityQueue()
    discovered = set()
    logs = []
    visited_paths = {}

    # breadth first search
    start_time = time.time()
    elapsed_time = time.time() - start_time
    queue.put((0, 0, start_page, [start_page], 0))  # Priority, similarity score, vertex, path, depth. Initialize with start_page
    while not queue.empty() and elapsed_time < TIMEOUT:
        _, similarity_score, vertex, path, depth = queue.get()
        if depth > MAX_DEPTH:
            continue  # Skip adding new links if maximum depth is exceeded
        for next in set(get_links(vertex)) - set(discovered.keys()):
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
                # Dynamic priority adjustment based on similarity score
                new_similarity_score = similarity_score + url_similarity(next, finish_page)
                new_priority = -1 * new_similarity_score  # Higher similarity gives a lower (more negative) priority
                # Limit queue size by pruning less promising paths
                if len(queue.queue) < max_queue_size or new_priority > queue.queue[-1][0]:
                    if len(queue.queue) >= max_queue_size:
                        queue.get()  # Remove the least promising path
                    visited_paths[next] = new_similarity_score
                    queue.put((new_priority, new_similarity_score, next, path + [next], depth + 1))
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
