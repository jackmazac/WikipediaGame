import aiohttp
import asyncio
from aiohttp import ClientSession, ClientTimeout
import backoff
from aiohttp.client_exceptions import ClientError, ClientResponseError, ServerTimeoutError

# Constants
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10
RATE_LIMIT = 1  # requests per second

# Backoff strategy for retries
def backoff_hdlr(details):
    print(f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries calling function {details['target'].__name__} with args {details['args']} and kwargs {details['kwargs']}")

# Exponential backoff retrying for transient issues
@backoff.on_exception(backoff.expo, ClientError, max_tries=MAX_RETRIES, on_backoff=backoff_hdlr)
async def fetch(url: str, session: ClientSession, method: str = 'GET', data=None, headers=None):
    timeout = ClientTimeout(total=TIMEOUT_SECONDS)
    try:
        async with session.request(method, url, data=data, headers=headers, timeout=timeout) as response:
            response.raise_for_status()  # Raises exception for 400/500 status codes
            return await response.text()
    except (ClientResponseError, ServerTimeoutError) as e:
        print(f"HTTP Error for URL {url}: {e}")
        raise
    except asyncio.TimeoutError:
        print(f"TimeoutError for URL {url}")
        raise
    except ClientError as e:
        print(f"ClientError for URL {url}: {e}")
        raise
    except Exception as e:
        print(f"Unhandled exception for URL {url}: {e}")
        raise

class AsyncHTTPClient:
    def __init__(self, rate_limit=RATE_LIMIT):
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.session = None

    async def __aenter__(self):
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get(self, url, **kwargs):
        async with self.semaphore:
            return await fetch(url, self.session, 'GET', **kwargs)

    async def post(self, url, data=None, headers=None):
        async with self.semaphore:
            return await fetch(url, self.session, 'POST', data=data, headers=headers)

# Utility function to use AsyncHTTPClient
async def fetch_url(url):
    async with AsyncHTTPClient() as client:
        content = await client.get(url)
        return content

# Example usage
async def main():
    url = 'https://en.wikipedia.org/wiki/Main_Page'
    try:
        content = await fetch_url(url)
        print(content)
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
