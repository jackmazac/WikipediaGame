import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import numpy as np
from bs4 import BeautifulSoup
import re
from hashlib import md5
import os
import json

class WikipediaTextFetcher:
    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_text(self, title):
        cache_file = self._cache_file_path(title)
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as file:
                    return json.load(file)['text']

            # Fetch from Wikipedia API if not cached
            params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'extracts',
                'explaintext': True,
                'exsectionformat': 'wiki'
            }
            response = requests.get(self.API_URL, params=params)
            response.raise_for_status()  # Raises HTTPError for bad responses
            data = response.json()
            page = next(iter(data['query']['pages'].values()))
            text = page.get('extract', '')

            with open(cache_file, 'w') as file:
                json.dump({'text': text}, file)
            return text
        except requests.exceptions.RequestException as e:
            print(f"Network error while fetching text for {title}: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decoding failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None

    def _cache_file_path(self, title):
        filename = md5(title.encode('utf-8')).hexdigest() + '.json'
        return os.path.join(self.cache_dir, filename)

class TextPreprocessor:
    def preprocess_text(self, text):
        try:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text()
            return re.sub(r'\s+', ' ', text).strip()
        except Exception as e:
            print(f"Error during text preprocessing: {e}")
        return text

class TextSimilarity:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.svd = TruncatedSVD(n_components=100)
        self.is_fitted = False

    def compute_similarity(self, text1, text2):
        try:
            if not self.is_fitted:
                self._fit_model([text1, text2])
            transformed_texts = self.vectorizer.transform([text1, text2])
            transformed_texts = self.svd.transform(transformed_texts)
            similarity = cosine_similarity(transformed_texts[0:1], transformed_texts[1:2])[0][0]
            return similarity
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0

    def _fit_model(self, texts):
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            self.svd.fit(tfidf_matrix)
            self.is_fitted = True
        except Exception as e:
            print(f"Error during model fitting: {e}")

def compute_textual_similarity(text1, text2):
    similarity_calculator = TextSimilarity()
    return similarity_calculator.compute_similarity(text1, text2)
