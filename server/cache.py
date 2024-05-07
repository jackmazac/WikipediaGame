import os
import json
import hashlib
from threading import Lock

class FileCache:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.lock = Lock()
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating cache directory {cache_dir}: {e}")

    def _get_cache_path(self, key):
        """Creates a file path safe from the key using MD5 hash."""
        hash_key = hashlib.md5(key.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{hash_key}.json")

    def exists(self, key):
        """Checks if the cached file exists for the given key."""
        try:
            return os.path.exists(self._get_cache_path(key))
        except Exception as e:
            print(f"Error checking existence of cache file for key {key}: {e}")
            return False

    def read(self, key):
        """Reads data from cache file if exists."""
        try:
            cache_file_path = self._get_cache_path(key)
            if self.exists(key):
                with self.lock, open(cache_file_path, 'r') as file:
                    return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from cache file {cache_file_path}: {e}")
        except Exception as e:
            print(f"Error reading cache file {cache_file_path}: {e}")
        return None

    def write(self, key, data):
        """Writes data to a cache file, overwriting any existing file."""
        try:
            cache_file_path = self._get_cache_path(key)
            with self.lock:
                with open(cache_file_path, 'w') as file:
                    json.dump(data, file)
        except json.JSONEncodeError as e:
            print(f"Error encoding data to JSON for cache file {cache_file_path}: {e}")
        except Exception as e:
            print(f"Error writing to cache file {cache_file_path}: {e}")

# Example usage of the FileCache
if __name__ == "__main__":
    cache = FileCache()
    url = "http://example.com"
    cache_data = {"content": "Example content", "links": ["http://example.com/page1", "http://example.com/page2"]}

    # Writing data to cache
    if not cache.exists(url):
        print("Data not found in cache. Caching now...")
        cache.write(url, cache_data)
    else:
        print("Data already cached.")

    # Reading data from cache
    cached_data = cache.read(url)
    if cached_data:
        print("Cached Data:", cached_data)
    else:
        print("No data found in cache.")
