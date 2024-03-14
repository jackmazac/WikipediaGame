import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import spacy
import re
import time

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Constants for search
TIMEOUT = 20
MAX_DEPTH = 5
MAX_LINKS_PER_LEVEL = 10
REQUEST_DELAY = 1  # Delay between requests in seconds

def extract_keywords(text):
    doc = nlp(text)
    return [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']]

def jaccard_similarity(list1, list2):
    intersection = set(list1).intersection(set(list2))
    union = set(list1).union(set(list2))
    return len(intersection) / float(len(union)) if union else 0

def fetch_page_text(url):
    try:
        time.sleep(REQUEST_DELAY)  # Politeness delay
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return ' '.join([p.text for p in soup.find_all('p')])
    except requests.RequestException as e:
        print(f"Error fetching page {url}: {e}")
        return ''

def get_links(page_url, target_keywords):
    try:
        time.sleep(REQUEST_DELAY)  # Politeness delay
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links_with_scores = []
        for a in soup.find_all('a', href=True):
            full_url = urljoin(page_url, a['href'])
            if re.match(r'^https://en.wikipedia.org/wiki/[^:]*$', full_url):
                link_text = ' '.join(a.stripped_strings)
                context_keywords = extract_keywords(link_text)
                similarity_score = jaccard_similarity(context_keywords, target_keywords)
                links_with_scores.append((full_url, similarity_score))
        links_with_scores.sort(key=lambda x: x[1], reverse=True)
        return [link for link, _ in links_with_scores[:MAX_LINKS_PER_LEVEL]]
    except requests.RequestException as e:
        print(f"Error fetching links from {page_url}: {e}")
        return []

def generate_target_content(start_page, finish_page):
    start_text = fetch_page_text(start_page)
    finish_text = fetch_page_text(finish_page)
    if not start_text or not finish_text:
        return ''
    start_keywords = extract_keywords(start_text)
    finish_keywords = extract_keywords(finish_text)
    combined_keywords = list(set(start_keywords + finish_keywords))
    return ' '.join(combined_keywords)

def find_path(start_page, finish_page):
    target_content = generate_target_content(start_page, finish_page)
    if not target_content:
        print("Failed to generate target content.")
        return None
    target_keywords = extract_keywords(target_content)
    queue = [(start_page, [start_page])]
    discovered = set([start_page])
    start_time = time.time()
    while queue and time.time() - start_time < TIMEOUT:
        current_page, path = queue.pop(0)
        if current_page == finish_page:
            return path
        try:
            links = get_links(current_page, target_keywords)
            for link in links:
                if link not in discovered:
                    discovered.add(link)
                    queue.append((link, path + [link]))
        except Exception as e:
            print(f"Error fetching or processing links from {current_page}: {e}")
    return None

class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered
