import re
import logging
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def normalize_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return urljoin(url, urlparse(url).path.replace('/wiki/', '').replace('_', ' '))
    except Exception as e:
        logging.error(f"Error normalizing URL {url}: {e}")
    return None

def extract_title(url):
    try:
        title = urlparse(url).path.split('/')[-1]
        if title:
            return title.replace('_', ' ')
    except Exception as e:
        logging.error(f"Error extracting title from URL {url}: {e}")
    return None

def clean_text(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style", "sup", "table", "div"]):
            script.decompose()
        text = soup.get_text()
        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        logging.error(f"Error cleaning HTML content: {e}")
    return ''

def parse_links(html_content, base_url="https://en.wikipedia.org"):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/wiki/') and ':' not in href:
                full_url = urljoin(base_url, href)
                links.add(full_url)
        return list(links)
    except Exception as e:
        logging.error(f"Error parsing links from HTML content: {e}")
    return []

def setup_logger(name='WikiCrawler', level=logging.INFO, file_name='crawler.log'):
    try:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        handler = logging.FileHandler(file_name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    except Exception as e:
        logging.error(f"Error setting up logger {name}: {e}")
    return logging.getLogger(name)  # Return a basic logger if setup fails

# Example usage
if __name__ == "__main__":
    example_url = "https://en.wikipedia.org/wiki/OpenAI"
    normalized_url = normalize_url(example_url)
    title = extract_title(normalized_url)
    logger = setup_logger()
    logger.info(f"Normalized URL: {normalized_url}, Title: {title}")
